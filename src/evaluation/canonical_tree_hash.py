"""Canonical, cross-platform hashing of on-disk artifact trees."""

from __future__ import annotations

import hashlib
from pathlib import Path


_TEXT_SUFFIXES = {".html", ".json", ".jsonl", ".md", ".txt", ".yaml", ".yml"}


def canonical_file_bytes(path: Path) -> bytes:
    """Return file bytes with text line endings normalised to LF."""

    body = path.read_bytes()
    if path.suffix.lower() in _TEXT_SUFFIXES:
        return body.replace(b"\r\n", b"\n")
    return body


def canonical_tree_hash(
    root: Path,
    *,
    ignore_names: frozenset[str] | None = None,
) -> tuple[str, int]:
    """Hash every file under ``root`` using POSIX-relative paths.

    Sorting and path encoding are repository-relative and OS-independent.
    Text bodies use LF for known text suffixes so Windows checkouts that still
    carry CRLF in the working tree cannot drift sealed hashes.
    """

    ignore = ignore_names or frozenset()
    digest = hashlib.sha256()
    count = 0
    files = sorted(
        (
            item.relative_to(root).as_posix(),
            item,
        )
        for item in root.rglob("*")
        if item.is_file() and item.name not in ignore
    )
    for relative, item in files:
        encoded = relative.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        body = canonical_file_bytes(item)
        digest.update(hashlib.sha256(body).digest())
        count += 1
    return digest.hexdigest(), count


def canonical_span_hash(
    root: Path, *, start_gameweek: int, end_gameweek: int
) -> tuple[str, int]:
    """Hash canonical ``gw-NN`` directories across an inclusive Gameweek span."""

    digest = hashlib.sha256()
    count = 0
    for gameweek in range(start_gameweek, end_gameweek + 1):
        directory = root / f"gw-{gameweek:02d}"
        if not directory.is_dir():
            raise FileNotFoundError(f"Missing canonical GW{gameweek}")
        files = sorted(
            (
                item.relative_to(root).as_posix(),
                item,
            )
            for item in directory.rglob("*")
            if item.is_file()
        )
        for relative, item in files:
            encoded = relative.encode("utf-8")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
            digest.update(hashlib.sha256(canonical_file_bytes(item)).digest())
            count += 1
    return digest.hexdigest(), count
