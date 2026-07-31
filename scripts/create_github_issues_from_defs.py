"""Create GitHub Issues from .github/issue-defs/manifest.yaml.

Idempotent: skips titles that already exist (open or closed).

Requires a collaborator-authenticated `gh` CLI. The Cursor cloud-agent
installation token cannot call createIssue; run this locally or via the
workflow_dispatch Action with permissions: issues: write.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is a project dependency
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
DEFS = ROOT / ".github" / "issue-defs"
MANIFEST = DEFS / "manifest.yaml"


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def _ensure_label(name: str, color: str, description: str) -> None:
    listed = _run(
        ["gh", "label", "list", "--json", "name", "--jq", ".[].name"],
        check=False,
    )
    if listed.returncode != 0:
        print(f"warning: could not list labels: {listed.stderr.strip()}", file=sys.stderr)
        return
    existing = {line.strip() for line in listed.stdout.splitlines() if line.strip()}
    if name in existing:
        return
    created = _run(
        [
            "gh",
            "label",
            "create",
            name,
            "--color",
            color,
            "--description",
            description,
        ],
        check=False,
    )
    if created.returncode != 0:
        print(
            f"warning: could not create label {name!r}: {created.stderr.strip()}",
            file=sys.stderr,
        )


def _existing_titles() -> set[str]:
    titles: set[str] = set()
    for state in ("open", "closed"):
        result = _run(
            [
                "gh",
                "issue",
                "list",
                "--state",
                state,
                "--limit",
                "500",
                "--json",
                "title",
            ],
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "gh issue list failed. Authenticate as a collaborator with "
                f"issues read/write access.\n{result.stderr.strip()}"
            )
        for item in json.loads(result.stdout or "[]"):
            titles.add(item["title"])
    return titles


def _load_manifest() -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML is required; install project dependencies first")
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


LABEL_META = {
    "p0": ("B60205", "Highest priority"),
    "p1": ("D93F0B", "High priority"),
    "p2": ("FBCA04", "Medium priority"),
    "p3": ("0E8A16", "Lower priority"),
    "epic": ("5319E7", "Epic / programme residual"),
    "owner-gated": ("BFDADC", "Needs owner decision before enablement"),
    "migrated-from-beads": ("C5DEF5", "Migrated from retired Beads tracker"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without creating issues or labels",
    )
    args = parser.parse_args(argv)

    manifest = _load_manifest()
    issues = manifest.get("issues") or []
    if not issues:
        print("No issues in manifest", file=sys.stderr)
        return 1

    if not args.dry_run:
        for name, (color, description) in LABEL_META.items():
            _ensure_label(name, color, description)

    existing = set() if args.dry_run else _existing_titles()
    created = 0
    skipped = 0

    for entry in issues:
        title = entry["title"]
        body_path = DEFS / entry["file"]
        if not body_path.is_file():
            print(f"error: missing body file {body_path}", file=sys.stderr)
            return 1
        body = body_path.read_text(encoding="utf-8")
        labels = entry.get("labels") or []

        if title in existing:
            print(f"skip (exists): {title}")
            skipped += 1
            continue

        if args.dry_run:
            print(f"dry-run create: {title}")
            print(f"  labels: {', '.join(labels)}")
            print(f"  body: {body_path.relative_to(ROOT)}")
            created += 1
            continue

        cmd = ["gh", "issue", "create", "--title", title, "--body-file", str(body_path)]
        for label in labels:
            cmd.extend(["--label", label])
        result = _run(cmd, check=False)
        if result.returncode != 0:
            print(f"error creating {title!r}: {result.stderr.strip()}", file=sys.stderr)
            return 1
        url = result.stdout.strip()
        print(f"created: {url}")
        existing.add(title)
        created += 1

    print(f"done: created={created} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
