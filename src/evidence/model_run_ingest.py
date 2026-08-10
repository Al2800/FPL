"""Host validation and admission for engine-model evidence runs.

The model may search and summarise official sources, but it does not write
directly to the decision ledger.  This module is the deterministic host gate:
it checks the run contract, catalogue coverage, exact player identity, source
rights and official domains, fetches each cited page ephemerally for a content
hash, and then appends only valid derived availability claims.

Page bodies are hashed in memory and discarded.  The model's concise claim,
relevance note and decision trace are retained so a later reader can see what
was considered and why without retaining a bulk article mirror or hidden
chain-of-thought.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yaml

from src.evidence.availability_ledger import (
    AvailabilityLedgerError,
    append_availability_claim,
    new_availability_ledger,
    validate_availability_ledger,
)
from src.evidence.lifecycle import scan_injection
from src.forecasting.live_faithful import artifact_hash


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = REPO_ROOT / "control" / "sources" / "source-registry.yaml"
DEFAULT_CATALOGUE_PATH = (
    REPO_ROOT / "control" / "sources" / "club-news-catalogue.yaml"
)
DEFAULT_POLICY_PATH = (
    REPO_ROOT / "config" / "data_sources" / "2026-27-model-evidence-run.json"
)
DEFAULT_BOOTSTRAP_PATH = (
    REPO_ROOT
    / "data"
    / "snapshots"
    / "2026-27"
    / "preseason"
    / "weekly-2026-08-02"
    / "raw"
    / "20260802T100000Z"
    / "bootstrap-static.json"
)
MODEL_RUN_SCHEMA_VERSION = "model-evidence-run-v1"
AUDIT_SCHEMA_VERSION = "model-evidence-ingest-audit-v1"
SHA256_LENGTH = 64
FetchSource = Callable[[str], str]


class ModelEvidenceRunError(ValueError):
    """Raised when an engine-model evidence run cannot be admitted safely."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ModelEvidenceRunError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise ModelEvidenceRunError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == SHA256_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _as_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelEvidenceRunError(f"Cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise ModelEvidenceRunError(f"{label} must be a JSON object: {path}")
    return value


def _load_yaml_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ModelEvidenceRunError(f"Cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise ModelEvidenceRunError(f"{label} must be a YAML object: {path}")
    return value


def _source_row(registry: Mapping[str, Any], source_id: str) -> Mapping[str, Any]:
    for row in registry.get("sources", []):
        if isinstance(row, Mapping) and row.get("source_id") == source_id:
            return row
    raise ModelEvidenceRunError(f"Evidence source is not registered: {source_id}")


def _policy_source(
    policy: Mapping[str, Any], source_id: str
) -> Mapping[str, Any]:
    for row in policy.get("sources", []):
        if isinstance(row, Mapping) and row.get("source_id") == source_id:
            return row
    raise ModelEvidenceRunError(
        f"Evidence source is not admitted to model-run policy: {source_id}"
    )


def _validate_source_admission(
    *,
    source_id: str,
    registry: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> Mapping[str, Any]:
    source = _source_row(registry, source_id)
    configured = _policy_source(policy, source_id)
    if source.get("enabled") is not True:
        raise ModelEvidenceRunError(f"Evidence source is disabled: {source_id}")
    if source.get("licence_status") in {"unknown", "prohibited"}:
        raise ModelEvidenceRunError(
            f"Evidence source rights are unresolved: {source_id}"
        )
    if not str(source.get("allowed_use", "")).strip():
        raise ModelEvidenceRunError(
            f"Evidence source has no allowed use: {source_id}"
        )
    if configured.get("admitted") is not True:
        raise ModelEvidenceRunError(
            f"Evidence source is not admitted to model-run policy: {source_id}"
        )
    if configured.get("admission_mode") != "model_assisted_citation":
        raise ModelEvidenceRunError(
            f"Evidence source does not use model-assisted citation mode: {source_id}"
        )
    model_run = source.get("model_run")
    if not isinstance(model_run, Mapping) or model_run.get("enabled") is not True:
        raise ModelEvidenceRunError(
            f"Evidence source has no enabled model-run path: {source_id}"
        )
    if model_run.get("raw_content_retained") is not False:
        raise ModelEvidenceRunError(
            f"Model-run source must discard raw content: {source_id}"
        )
    return source


def _official_domains(catalogue: Mapping[str, Any]) -> set[str]:
    domains: set[str] = set()
    for row in catalogue.get("sources", []):
        if not isinstance(row, Mapping):
            continue
        domain = str(row.get("official_domain", "")).strip().lower()
        if domain:
            domains.add(domain.removeprefix("www."))
    if not domains:
        raise ModelEvidenceRunError("News catalogue has no official domains")
    return domains


def _catalogue_ids(catalogue: Mapping[str, Any]) -> set[str]:
    result = {
        str(row["club_id"])
        for row in catalogue.get("sources", [])
        if isinstance(row, Mapping) and row.get("club_id")
    }
    if not result:
        raise ModelEvidenceRunError("News catalogue has no club IDs")
    return result


def _validate_official_url(url: str, domains: set[str]) -> None:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().removeprefix("www.")
    if parsed.scheme != "https" or not hostname or parsed.username or parsed.password:
        raise ModelEvidenceRunError("source_url must be a canonical HTTPS URL")
    if hostname not in domains and not any(
        hostname.endswith(f".{domain}") for domain in domains
    ):
        raise ModelEvidenceRunError(
            f"source_url is outside the registered official catalogue: {url}"
        )


def fetch_source_hash(url: str, *, timeout_seconds: float = 20.0, max_bytes: int = 5_000_000) -> str:
    """Fetch only enough bytes to hash a cited page; never writes the body."""

    request = Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "FPL-Agentic-Decision-Lab/1.0 (private analysis)",
        },
    )
    digest = hashlib.sha256()
    total = 0
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            while True:
                chunk = response.read(65_536)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ModelEvidenceRunError(
                        f"source page exceeds ephemeral hash limit: {url}"
                    )
                digest.update(chunk)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ModelEvidenceRunError(
            f"ephemeral source fetch failed for {url}: {exc}"
        ) from exc
    if total == 0:
        raise ModelEvidenceRunError(f"ephemeral source fetch was empty: {url}")
    return digest.hexdigest()


def _validate_prompt_binding(
    prompt: Mapping[str, Any], *, repo_root: Path
) -> str:
    path_value = prompt.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise ModelEvidenceRunError("model run prompt.path is required")
    prompt_path = Path(path_value)
    if not prompt_path.is_absolute():
        prompt_path = repo_root / prompt_path
    if not prompt_path.is_file():
        raise ModelEvidenceRunError(f"model run prompt is missing: {prompt_path}")
    actual = _sha256_bytes(prompt_path.read_bytes())
    if prompt.get("sha256") != actual:
        raise ModelEvidenceRunError(
            f"model run prompt hash mismatch: {prompt_path}"
        )
    if not str(prompt.get("version", "")).strip():
        raise ModelEvidenceRunError("model run prompt.version is required")
    return actual


def _validate_shape(model_run: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "run_id",
        "model",
        "prompt",
        "observed_at",
        "available_at",
        "bound_packet_sha256",
        "discovery_sha256",
        "scope",
        "coverage",
        "claims",
        "decision_trace",
    }
    missing = sorted(required - set(model_run))
    if missing:
        raise ModelEvidenceRunError(
            "model evidence run missing fields: " + ", ".join(missing)
        )
    if model_run["schema_version"] != MODEL_RUN_SCHEMA_VERSION:
        raise ModelEvidenceRunError("unsupported model evidence run schema")
    if not str(model_run["run_id"]).strip():
        raise ModelEvidenceRunError("model evidence run_id is required")
    model = model_run["model"]
    if not isinstance(model, Mapping) or not str(model.get("id", "")).strip():
        raise ModelEvidenceRunError("model evidence run model.id is required")
    observed = _timestamp(model_run["observed_at"], "observed_at")
    available = _timestamp(model_run["available_at"], "available_at")
    if available < observed:
        raise ModelEvidenceRunError("model run available_at precedes observed_at")
    packet_hash = model_run["bound_packet_sha256"]
    if packet_hash is not None and not _is_sha256(packet_hash):
        raise ModelEvidenceRunError(
            "bound_packet_sha256 must be null or a lower-case SHA-256"
        )
    if not _is_sha256(model_run["discovery_sha256"]):
        raise ModelEvidenceRunError("discovery_sha256 must be a SHA-256")
    scope = model_run["scope"]
    if not isinstance(scope, Mapping):
        raise ModelEvidenceRunError("model evidence run scope must be an object")
    if not _is_sha256(scope.get("catalogue_sha256")):
        raise ModelEvidenceRunError("scope.catalogue_sha256 must be a SHA-256")
    for field in ("searched_club_ids", "watchlist_player_uids"):
        values = scope.get(field)
        if not isinstance(values, list) or not values or any(
            not isinstance(value, str) or not value for value in values
        ):
            raise ModelEvidenceRunError(
                f"scope.{field} must be a non-empty string list"
            )
    if not str(scope.get("watchlist_basis", "")).strip():
        raise ModelEvidenceRunError("scope.watchlist_basis is required")
    coverage = model_run["coverage"]
    if not isinstance(coverage, Mapping):
        raise ModelEvidenceRunError("model evidence run coverage must be an object")
    claims = model_run["claims"]
    if not isinstance(claims, list):
        raise ModelEvidenceRunError("model evidence run claims must be a list")
    for index, claim in enumerate(claims):
        if not isinstance(claim, Mapping):
            raise ModelEvidenceRunError(f"claim[{index}] must be an object")
        required_claim = {
            "claim_id",
            "club_id",
            "player_uid",
            "source_id",
            "source_url",
            "source_title",
            "claim_text",
            "why_relevant",
            "claim_type",
            "status",
            "confidence",
            "published_at",
            "expires_at",
        }
        missing_claim = sorted(required_claim - set(claim))
        if missing_claim:
            raise ModelEvidenceRunError(
                f"claim[{index}] missing fields: " + ", ".join(missing_claim)
            )
        for field in (
            "claim_id",
            "club_id",
            "player_uid",
            "source_id",
            "source_url",
            "source_title",
            "claim_text",
            "why_relevant",
        ):
            if not isinstance(claim[field], str) or not claim[field].strip():
                raise ModelEvidenceRunError(
                    f"claim[{index}].{field} must be a non-empty string"
                )
        if len(claim["claim_text"]) > 500 or len(claim["why_relevant"]) > 500:
            raise ModelEvidenceRunError(
                f"claim[{index}] exceeds derived-text limits"
            )
        if claim["status"] not in {"unavailable", "doubtful", "available"}:
            raise ModelEvidenceRunError(f"claim[{index}] has invalid status")
        if claim["claim_type"] not in {"availability", "minutes_role", "lineup"}:
            raise ModelEvidenceRunError(f"claim[{index}] has invalid claim_type")
        confidence = claim["confidence"]
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (float, int))
            or not 0 <= float(confidence) <= 1
        ):
            raise ModelEvidenceRunError(
                f"claim[{index}].confidence must be between zero and one"
            )
        published = _timestamp(claim["published_at"], f"claim[{index}].published_at")
        expires = _timestamp(claim["expires_at"], f"claim[{index}].expires_at")
        if expires <= published:
            raise ModelEvidenceRunError(
                f"claim[{index}].expires_at must follow publication"
            )
        injection = scan_injection(claim["claim_text"])
        if injection.quarantined:
            raise ModelEvidenceRunError(
                f"claim[{index}] contains prompt-injection-like text"
            )
    trace = model_run["decision_trace"]
    if not isinstance(trace, list):
        raise ModelEvidenceRunError("decision_trace must be a list")
    for index, item in enumerate(trace):
        if not isinstance(item, Mapping):
            raise ModelEvidenceRunError(f"decision_trace[{index}] must be an object")
        required_trace = {
            "boundary_id",
            "decision",
            "rationale",
            "alternatives_rejected",
            "supporting_claim_ids",
            "conflicting_claim_ids",
            "confidence",
            "falsifiers",
        }
        missing_trace = sorted(required_trace - set(item))
        if missing_trace:
            raise ModelEvidenceRunError(
                f"decision_trace[{index}] missing fields: "
                + ", ".join(missing_trace)
            )
        if not str(item["rationale"]).strip():
            raise ModelEvidenceRunError(
                f"decision_trace[{index}].rationale is required"
            )
        if len(str(item["rationale"])) > 1000:
            raise ModelEvidenceRunError(
                f"decision_trace[{index}].rationale exceeds 1000 characters"
            )


def _player_ids(
    bootstrap: Mapping[str, Any], *, season: str
) -> set[str]:
    elements = bootstrap.get("elements")
    if not isinstance(elements, list) or not elements:
        raise ModelEvidenceRunError("bootstrap elements are required for exact identity")
    result: set[str] = set()
    for row in elements:
        if isinstance(row, Mapping) and row.get("id") is not None:
            try:
                result.add(f"player:{season}:{int(row['id'])}")
            except (TypeError, ValueError) as exc:
                raise ModelEvidenceRunError(
                    "bootstrap contains a non-integer player ID"
                ) from exc
    if not result:
        raise ModelEvidenceRunError("bootstrap has no player identities")
    return result


def _prior_matching_claim(
    ledger: Mapping[str, Any],
    *,
    player_uid: str,
    source_id: str,
    status: str,
    available_at: str,
) -> str | None:
    candidate_time = _timestamp(available_at, "claim.available_at")
    superseded = {
        str(value)
        for row in ledger["claims"]
        for value in row.get("supersedes_claim_ids", [])
    }
    matching = []
    for row in ledger["claims"]:
        if (
            row.get("player_uid") == player_uid
            and row.get("status") == status
            and source_id in row.get("provenance", {}).get("source_ids", [])
            and row.get("claim_id") not in superseded
        ):
            row_time = _timestamp(row["available_at"], "available_at")
            if row_time < candidate_time:
                matching.append((row_time, str(row["claim_id"])))
    if not matching:
        return None
    return max(matching)[1]


def _claim_fingerprint(
    *,
    source_url: str,
    source_hash: str,
    player_uid: str,
    status: str,
    published_at: str,
    claim_type: str,
) -> str:
    return _sha256_json(
        {
            "source_url": source_url,
            "source_hash": source_hash,
            "player_uid": player_uid,
            "status": status,
            "published_at": published_at,
            "claim_type": claim_type,
        }
    )


def _new_claim(
    candidate: Mapping[str, Any],
    *,
    canonical_id: str,
    source_hash: str,
    model_run: Mapping[str, Any],
    model_run_sha256: str,
    supersedes: str | None,
) -> dict[str, Any]:
    provenance = {
        "source_ids": [str(candidate["source_id"])],
        "urls": [str(candidate["source_url"])],
        "source_document_hash_sha256": source_hash,
        "hash_basis": "ephemeral_fetched_source_body_discarded_after_hash",
        "transformation_version": "model-evidence-ingest-v1",
        "identity_resolution": "exact",
        "model_run_id": str(model_run["run_id"]),
        "model_id": str(model_run["model"]["id"]),
        "prompt_path": str(model_run["prompt"]["path"]),
        "prompt_version": str(model_run["prompt"]["version"]),
        "model_run_sha256": model_run_sha256,
        "derived_claim": str(candidate["claim_text"]),
        "why_relevant": str(candidate["why_relevant"]),
        "source_title": str(candidate["source_title"]),
    }
    claim: dict[str, Any] = {
        "claim_id": canonical_id,
        "player_uid": str(candidate["player_uid"]),
        "status": str(candidate["status"]),
        "confidence": float(candidate["confidence"]),
        "published_at": str(candidate["published_at"]),
        "observed_at": str(model_run["observed_at"]),
        "available_at": str(model_run["available_at"]),
        "expires_at": str(candidate["expires_at"]),
        "provenance": provenance,
    }
    if supersedes:
        claim["supersedes_claim_ids"] = [supersedes]
    if candidate["status"] == "available":
        condition = candidate.get("recovery_condition")
        if condition:
            claim["recovery"] = {
                "condition": str(condition),
                "observed_at": str(model_run["available_at"]),
            }
    return claim


def ingest_model_evidence_run(
    model_run: Mapping[str, Any],
    current_ledger: Mapping[str, Any] | None,
    *,
    source_registry: Mapping[str, Any],
    policy: Mapping[str, Any],
    catalogue: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    discovery: Mapping[str, Any] | None = None,
    model_run_sha256: str | None = None,
    fetcher: FetchSource | None = None,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate a model run and return the new ledger plus an admission audit."""

    _validate_shape(model_run)
    prompt_sha256 = _validate_prompt_binding(
        model_run["prompt"], repo_root=repo_root
    )
    season = str(bootstrap.get("season", "2026-27"))
    player_ids = _player_ids(bootstrap, season=season)
    catalogue_ids = _catalogue_ids(catalogue)
    domains = _official_domains(catalogue)
    expected_catalogue_hash = _sha256_bytes(
        json.dumps(catalogue, sort_keys=True, ensure_ascii=False).encode("utf-8")
    )
    scope = model_run["scope"]
    coverage_gaps = sorted(
        catalogue_ids - {str(value) for value in scope["searched_club_ids"]}
    )
    unknown_searched = sorted(
        {str(value) for value in scope["searched_club_ids"]} - catalogue_ids
    )
    if scope["catalogue_sha256"] != expected_catalogue_hash:
        raise ModelEvidenceRunError("model run catalogue hash mismatch")
    if unknown_searched:
        raise ModelEvidenceRunError(
            "model run contains unknown searched club IDs: "
            + ", ".join(unknown_searched)
        )
    coverage = model_run["coverage"]
    missing_coverage_rows = sorted(catalogue_ids - set(coverage))
    if missing_coverage_rows:
        coverage_gaps = sorted(set(coverage_gaps) | set(missing_coverage_rows))
    discovery_urls: set[str] | None = None
    discovery_coverage_gaps: set[str] = set()
    if discovery is not None:
        if discovery.get("content_sha256") != artifact_hash(discovery):
            raise ModelEvidenceRunError("discovery artifact hash mismatch")
        if discovery.get("content_sha256") != model_run["discovery_sha256"]:
            raise ModelEvidenceRunError(
                "model run discovery hash does not match discovery artifact"
            )
        discovery_coverage = discovery.get("coverage")
        if not isinstance(discovery_coverage, list):
            raise ModelEvidenceRunError("discovery coverage must be a list")
        discovered_clubs = set()
        for row in discovery_coverage:
            if not isinstance(row, Mapping) or not row.get("club_id"):
                raise ModelEvidenceRunError("discovery coverage row is malformed")
            club_id = str(row["club_id"])
            if club_id not in catalogue_ids:
                raise ModelEvidenceRunError(
                    f"discovery contains unknown club ID: {club_id}"
                )
            if row.get("status") == "searched":
                discovered_clubs.add(club_id)
            else:
                discovery_coverage_gaps.add(club_id)
        if discovered_clubs - set(scope["searched_club_ids"]):
            raise ModelEvidenceRunError(
                "model run scope omits clubs present in discovery coverage"
            )
        discovery_urls = {
            str(row["source_url"])
            for row in discovery.get("leads", [])
            if isinstance(row, Mapping) and row.get("source_url")
        }
        coverage_gaps = sorted(
            set(coverage_gaps) | discovery_coverage_gaps
        )
    policy_run = policy.get("model_run", {})
    accepted_models = {
        str(value)
        for value in policy_run.get("accepted_model_ids", [])
        if isinstance(value, str)
    }
    if accepted_models and str(model_run["model"]["id"]) not in accepted_models:
        raise ModelEvidenceRunError(
            "model is not admitted to the model-evidence run policy: "
            + str(model_run["model"]["id"])
        )
    max_claims = int(policy_run.get("max_claims_per_run", 120))
    if len(model_run["claims"]) > max_claims:
        raise ModelEvidenceRunError(
            f"model run contains {len(model_run['claims'])} claims; "
            f"maximum is {max_claims}"
        )
    max_trace_items = int(policy_run.get("max_decision_trace_items", 40))
    if len(model_run["decision_trace"]) > max_trace_items:
        raise ModelEvidenceRunError(
            f"model run contains {len(model_run['decision_trace'])} decision-trace "
            f"items; maximum is {max_trace_items}"
        )
    minimum_watchlist = int(policy_run.get("minimum_watchlist_players", 40))
    watchlist = {str(value) for value in scope["watchlist_player_uids"]}
    invalid_watchlist = sorted(watchlist - player_ids)
    if invalid_watchlist:
        raise ModelEvidenceRunError(
            "model run watchlist contains unknown player IDs: "
            + ", ".join(invalid_watchlist[:5])
        )
    if len(watchlist) < minimum_watchlist:
        raise ModelEvidenceRunError(
            f"model run watchlist has {len(watchlist)} players; "
            f"minimum is {minimum_watchlist}"
        )
    if current_ledger is None:
        ledger = new_availability_ledger(
            season=season, created_at=str(model_run["available_at"])
        )
        prior_ledger_sha256 = None
    else:
        ledger = deepcopy(dict(current_ledger))
        validate_availability_ledger(ledger)
        if ledger.get("season") != season:
            raise ModelEvidenceRunError("current ledger season does not match bootstrap")
        prior_ledger_sha256 = str(ledger["content_sha256"])
    threshold = float(
        policy.get("thresholds", {}).get("minimum_claim_confidence", 0.55)
    )
    fetch = fetcher or (
        lambda url: fetch_source_hash(
            url,
            timeout_seconds=float(policy_run.get("fetch_timeout_seconds", 20)),
            max_bytes=int(policy_run.get("max_source_bytes", 5_000_000)),
        )
    )
    run_hash = model_run_sha256 or _sha256_json(model_run)
    fetched: dict[str, str] = {}
    accepted: list[str] = []
    duplicate: list[str] = []
    rejected: list[dict[str, Any]] = []
    claim_id_map: dict[str, str] = {}
    candidates = sorted(
        list(model_run["claims"]),
        key=lambda row: (str(row["published_at"]), str(row["claim_id"])),
    )
    for candidate in candidates:
        candidate_id = str(candidate["claim_id"])
        reasons: list[str] = []
        try:
            if candidate["confidence"] < threshold:
                reasons.append("confidence_below_policy_threshold")
            if candidate["club_id"] not in catalogue_ids:
                reasons.append("club_not_in_catalogue")
            elif candidate["club_id"] not in scope["searched_club_ids"]:
                reasons.append("club_not_searched_in_run")
            if candidate["player_uid"] not in player_ids:
                reasons.append("player_identity_not_exact")
            elif candidate["player_uid"] not in watchlist:
                reasons.append("player_not_in_declared_watchlist")
            if (
                discovery_urls is not None
                and candidate["source_url"] not in discovery_urls
            ):
                reasons.append("source_url_not_in_discovery_artifact")
            if candidate["source_id"] not in {
                str(row["source_id"])
                for row in policy.get("sources", [])
                if isinstance(row, Mapping)
            }:
                reasons.append("source_not_in_model_run_policy")
            if not reasons:
                _validate_source_admission(
                    source_id=str(candidate["source_id"]),
                    registry=source_registry,
                    policy=policy,
                )
                _validate_official_url(str(candidate["source_url"]), domains)
                if candidate["status"] == "available" and not candidate.get(
                    "recovery_condition"
                ):
                    reasons.append("available_claim_missing_recovery_condition")
            if not reasons:
                url = str(candidate["source_url"])
                if url not in fetched:
                    fetched[url] = fetch(url)
                source_hash = fetched[url]
                fingerprint = _claim_fingerprint(
                    source_url=url,
                    source_hash=source_hash,
                    player_uid=str(candidate["player_uid"]),
                    status=str(candidate["status"]),
                    published_at=str(candidate["published_at"]),
                    claim_type=str(candidate["claim_type"]),
                )
                canonical_id = f"model:{fingerprint}"
                claim_id_map[candidate_id] = canonical_id
                if any(
                    str(row["claim_id"]) == canonical_id for row in ledger["claims"]
                ):
                    duplicate.append(canonical_id)
                    continue
                supersedes = _prior_matching_claim(
                    ledger,
                    player_uid=str(candidate["player_uid"]),
                    source_id=str(candidate["source_id"]),
                    status=str(candidate["status"]),
                    available_at=str(model_run["available_at"]),
                )
                claim = _new_claim(
                    candidate,
                    canonical_id=canonical_id,
                    source_hash=source_hash,
                    model_run=model_run,
                    model_run_sha256=run_hash,
                    supersedes=supersedes,
                )
                ledger = append_availability_claim(ledger, claim)
                accepted.append(canonical_id)
        except (ModelEvidenceRunError, AvailabilityLedgerError, KeyError, TypeError) as exc:
            reasons.append(str(exc))
        if reasons:
            rejected.append(
                {
                    "candidate_claim_id": candidate_id,
                    "club_id": str(candidate.get("club_id", "")),
                    "player_uid": str(candidate.get("player_uid", "")),
                    "source_url": str(candidate.get("source_url", "")),
                    "claim_text": str(candidate.get("claim_text", "")),
                    "why_relevant": str(candidate.get("why_relevant", "")),
                    "reasons": sorted(set(reasons)),
                }
            )
    trace = deepcopy(list(model_run["decision_trace"]))
    for item in trace:
        for field in ("supporting_claim_ids", "conflicting_claim_ids"):
            item[field] = [
                claim_id_map.get(str(value), str(value)) for value in item[field]
            ]
    review_flags: list[str] = []
    if coverage_gaps:
        review_flags.append("incomplete_catalogue_coverage")
    if rejected:
        review_flags.append("model_candidates_rejected")
    if not accepted and model_run["claims"]:
        review_flags.append("no_new_claims_admitted")
    if trace and not any(
        item.get("supporting_claim_ids") or item.get("conflicting_claim_ids")
        for item in trace
    ):
        review_flags.append("decision_trace_has_no_claim_links")
    if model_run["claims"] and not fetched:
        review_flags.append("no_official_documents_hashed")
    acceptance_rate = (
        len(accepted) / len(model_run["claims"]) if model_run["claims"] else 0.0
    )
    audit = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "run_id": str(model_run["run_id"]),
        "model": deepcopy(dict(model_run["model"])),
        "prompt": deepcopy(dict(model_run["prompt"])),
        "prompt_sha256_verified": prompt_sha256,
        "model_run_sha256": run_hash,
        "prior_ledger_sha256": prior_ledger_sha256,
        "bound_packet_sha256": model_run["bound_packet_sha256"],
        "discovery_sha256": model_run["discovery_sha256"],
        "observed_at": str(model_run["observed_at"]),
        "available_at": str(model_run["available_at"]),
        "source_policy": "model_assisted_ephemeral_citation",
        "discovery_binding_verified": discovery is not None,
        "coverage": {
            "catalogue_club_count": len(catalogue_ids),
            "searched_club_count": len(scope["searched_club_ids"]),
            "coverage_gaps": coverage_gaps,
            "watchlist_player_count": len(watchlist),
        },
        "fetched_documents": [
            {"source_url": url, "source_hash_sha256": digest}
            for url, digest in sorted(fetched.items())
        ],
        "signal_checks": {
            "candidate_count": len(model_run["claims"]),
            "accepted_count": len(accepted),
            "duplicate_count": len(duplicate),
            "rejected_count": len(rejected),
            "acceptance_rate": round(acceptance_rate, 6),
            "decision_trace_count": len(trace),
            "decision_trace_linked_count": sum(
                bool(
                    item.get("supporting_claim_ids")
                    or item.get("conflicting_claim_ids")
                )
                for item in trace
            ),
            "review_flags": review_flags,
        },
        "accepted_claim_ids": accepted,
        "candidate_claim_bindings": claim_id_map,
        "duplicate_claim_ids": duplicate,
        "rejected_claims": rejected,
        "decision_trace": trace,
        "resulting_ledger_sha256": str(ledger["content_sha256"]),
        "status": (
            "complete"
            if not coverage_gaps and not rejected
            else "degraded"
        ),
    }
    audit["content_sha256"] = artifact_hash(audit)
    return ledger, audit


def discover_latest_availability_ledger(root: Path) -> Path | None:
    """Find the ledger with the latest available claim in a local evidence root."""

    candidates = [
        path
        for path in root.glob("*.json")
        if not path.name.endswith(".audit.json")
        and path.name != "latest-ledger.json"
    ]
    ranked: list[tuple[datetime, str, Path]] = []
    for path in candidates:
        try:
            value = _read_object(path, "availability ledger")
            validate_availability_ledger(value)
            latest = max(
                (
                    _timestamp(row["available_at"], "available_at")
                    for row in value["claims"]
                ),
                default=_timestamp(value["created_at"], "created_at"),
            )
            ranked.append((latest, str(value["content_sha256"]), path))
        except (ModelEvidenceRunError, AvailabilityLedgerError):
            continue
    if not ranked:
        return None
    return max(ranked)[2]


def write_immutable_json(path: Path, value: Mapping[str, Any]) -> None:
    """Write one content-addressed operational artifact without overwriting."""

    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
    except FileExistsError:
        if path.read_bytes() != encoded:
            raise ModelEvidenceRunError(
                f"immutable model-run artifact differs: {path}"
            )


def render_model_evidence_review(
    audit: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> str:
    """Render a human-readable, deterministic review of one model run."""

    def md(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    validate_availability_ledger(ledger)
    if audit.get("schema_version") != AUDIT_SCHEMA_VERSION:
        raise ModelEvidenceRunError("unsupported model-evidence audit schema")
    accepted_ids = {str(value) for value in audit.get("accepted_claim_ids", [])}
    duplicate_ids = {str(value) for value in audit.get("duplicate_claim_ids", [])}
    accepted_claims = [
        row for row in ledger["claims"] if str(row["claim_id"]) in accepted_ids
    ]
    status_counts: dict[str, int] = {}
    for row in accepted_claims:
        status = str(row["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    candidate_count = (
        len(accepted_ids)
        + len(duplicate_ids)
        + len(audit.get("rejected_claims", []))
    )
    coverage = audit.get("coverage", {})
    searched = int(coverage.get("searched_club_count", 0))
    catalogue = int(coverage.get("catalogue_club_count", 0))
    coverage_percent = (100.0 * searched / catalogue) if catalogue else 0.0
    trace = list(audit.get("decision_trace", []))
    trace_with_claims = sum(
        bool(item.get("supporting_claim_ids") or item.get("conflicting_claim_ids"))
        for item in trace
        if isinstance(item, Mapping)
    )
    lines = [
        f"# Model evidence run review — {audit.get('run_id', 'unknown')}",
        "",
        f"- status: **{audit.get('status', 'unknown')}**",
        f"- model: {audit.get('model', {}).get('display_name', audit.get('model', {}).get('id', 'unknown'))}",
        f"- observed_at: {audit.get('observed_at', 'unknown')}",
        f"- available_at: {audit.get('available_at', 'unknown')}",
        f"- bound_packet_sha256: {audit.get('bound_packet_sha256') or 'unavailable'}",
        f"- discovery_sha256: {audit.get('discovery_sha256', 'unknown')}",
        f"- model_run_sha256: {audit.get('model_run_sha256', 'unknown')}",
        f"- prior_ledger_sha256: {audit.get('prior_ledger_sha256') or 'none'}",
        f"- resulting_ledger_sha256: {audit.get('resulting_ledger_sha256', 'unknown')}",
        "",
        "## Signal capture checks",
        "",
        "| check | result |",
        "|---|---|",
        f"| Catalogue coverage | {searched}/{catalogue} clubs ({coverage_percent:.1f}%) |",
        f"| Coverage gaps | {', '.join(coverage.get('coverage_gaps', [])) or 'none'} |",
        f"| Watchlist size | {coverage.get('watchlist_player_count', 0)} players |",
        f"| Candidate claims | {candidate_count} |",
        f"| Accepted claims | {len(accepted_ids)} |",
        f"| Acceptance rate | {float(audit.get('signal_checks', {}).get('acceptance_rate', 0.0)):.1%} |",
        f"| Duplicate claims | {len(duplicate_ids)} |",
        f"| Rejected claims | {len(audit.get('rejected_claims', []))} |",
        f"| Ephemeral documents hashed | {len(audit.get('fetched_documents', []))} |",
        f"| Decision trace | {len(trace)} items; {trace_with_claims} linked to claims |",
        f"| Accepted statuses | {', '.join(f'{key}={value}' for key, value in sorted(status_counts.items())) or 'none'} |",
        f"| Review flags | {', '.join(audit.get('signal_checks', {}).get('review_flags', [])) or 'none'} |",
        "",
        "## Accepted ledger signal",
        "",
    ]
    if accepted_claims:
        lines.extend(
            [
                "| player | status | confidence | expires | derived claim | source |",
                "|---|---|---:|---|---|---|",
            ]
        )
        for row in accepted_claims:
            provenance = row.get("provenance", {})
            lines.append(
                "| "
                + " | ".join(
                    [
                        md(row["player_uid"]),
                        md(row["status"]),
                        f"{float(row['confidence']):.2f}",
                        md(row["expires_at"]),
                        md(provenance.get("derived_claim", "")),
                        md(provenance.get("urls", [""])[0]),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No claims were admitted.")
    lines.extend(["", "## Rejected or unresolved signal", ""])
    rejected = list(audit.get("rejected_claims", []))
    if rejected:
        lines.extend(
            [
                "| candidate | player | claim | reasons |",
                "|---|---|---|---|",
            ]
        )
        for row in rejected:
            lines.append(
                "| "
                + " | ".join(
                    [
                        md(row.get("candidate_claim_id", "")),
                        md(row.get("player_uid", "")),
                        md(row.get("claim_text", "")),
                        md(", ".join(str(reason) for reason in row.get("reasons", []))),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No candidates were rejected.")
    lines.extend(["", "## Decision rationale trace", ""])
    if trace:
        lines.extend(
            [
                "| boundary | decision | rationale | supporting claims | conflicting claims | confidence | falsifiers |",
                "|---|---|---|---|---|---:|---|",
            ]
        )
        for item in trace:
            lines.append(
                "| "
                + " | ".join(
                    [
                        md(item.get("boundary_id", "")),
                        md(item.get("decision", "")),
                        md(item.get("rationale", "")),
                        md(", ".join(str(value) for value in item.get("supporting_claim_ids", []))),
                        md(", ".join(str(value) for value in item.get("conflicting_claim_ids", []))),
                        f"{float(item.get('confidence', 0.0)):.2f}",
                        md("; ".join(str(value) for value in item.get("falsifiers", []))),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No decision trace was emitted.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a host audit of model-proposed signal, not an approval or",
            "  claim that the model's underlying football judgement is correct.",
            "- Community and unregistered sources remain briefing-only.",
            "- Raw source bodies are not retained; URLs, derived claims, hashes and",
            "  rejection reasons are the available review record.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_immutable_text(path: Path, text: str) -> None:
    """Write one human-readable review without overwriting a prior run."""

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text)
    except FileExistsError:
        if path.read_text(encoding="utf-8") != text:
            raise ModelEvidenceRunError(
                f"immutable model-run review differs: {path}"
            )


def safe_review_stem(run_id: str) -> str:
    """Make a portable report filename from an engine run ID."""

    return re.sub(r"[^A-Za-z0-9._-]+", "-", run_id).strip("-") or "model-run"
