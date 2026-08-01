#!/usr/bin/env python3
"""Admit one engine-model evidence run through the deterministic host gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.evidence.model_run_ingest import (  # noqa: E402
    DEFAULT_BOOTSTRAP_PATH,
    DEFAULT_CATALOGUE_PATH,
    DEFAULT_POLICY_PATH,
    DEFAULT_REGISTRY_PATH,
    ModelEvidenceRunError,
    discover_latest_availability_ledger,
    ingest_model_evidence_run,
    write_immutable_json,
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelEvidenceRunError(f"Cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise ModelEvidenceRunError(f"{label} must be a JSON object: {path}")
    return value


def _read_yaml(path: Path, label: str) -> dict:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ModelEvidenceRunError(f"Cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise ModelEvidenceRunError(f"{label} must be a YAML object: {path}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-output", type=Path, required=True)
    parser.add_argument("--current-ledger", type=Path)
    parser.add_argument(
        "--ledger-root",
        type=Path,
        default=REPO_ROOT / "data" / "live-shadow" / "availability",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO_ROOT / "data" / "live-shadow" / "availability" / "model-runs",
    )
    parser.add_argument("--bootstrap", type=Path, default=DEFAULT_BOOTSTRAP_PATH)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE_PATH)
    parser.add_argument("--discovery", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    args = parser.parse_args(argv)

    try:
        run_bytes = args.run_output.read_bytes()
        model_run = json.loads(run_bytes.decode("utf-8"))
        if not isinstance(model_run, dict):
            raise ModelEvidenceRunError("model run output must be a JSON object")
        current_path = args.current_ledger
        if current_path is None:
            current_path = discover_latest_availability_ledger(args.ledger_root)
        current = _read_json(current_path, "current availability ledger") if current_path else None
        bootstrap = _read_json(args.bootstrap, "official bootstrap")
        catalogue = _read_yaml(args.catalogue, "club news catalogue")
        discovery = _read_json(args.discovery, "news discovery artifact")
        registry = _read_yaml(args.registry, "source registry")
        policy = _read_json(args.policy, "model-run evidence policy")
        ledger, audit = ingest_model_evidence_run(
            model_run,
            current,
            source_registry=registry,
            policy=policy,
            catalogue=catalogue,
            bootstrap=bootstrap,
            discovery=discovery,
            model_run_sha256=_sha256_bytes(run_bytes),
            repo_root=REPO_ROOT,
        )
        args.output_root.mkdir(parents=True, exist_ok=True)
        ledger_path = args.output_root / (
            f"availability-ledger-{ledger['content_sha256']}.json"
        )
        audit_path = args.output_root / f"{model_run['run_id']}.audit.json"
        write_immutable_json(ledger_path, ledger)
        write_immutable_json(audit_path, audit)
        print(
            json.dumps(
                {
                    "status": audit["status"],
                    "run_id": audit["run_id"],
                    "ledger_path": str(ledger_path),
                    "ledger_sha256": ledger["content_sha256"],
                    "audit_path": str(audit_path),
                    "accepted_claims": len(audit["accepted_claim_ids"]),
                    "duplicate_claims": len(audit["duplicate_claim_ids"]),
                    "rejected_claims": len(audit["rejected_claims"]),
                    "coverage_gaps": audit["coverage"]["coverage_gaps"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    except (ModelEvidenceRunError, OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
