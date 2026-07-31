"""Portable contracts for cross-platform artifact tree hashing."""

from __future__ import annotations

from pathlib import Path

from src.evaluation.canonical_tree_hash import canonical_tree_hash


def test_canonical_tree_hash_is_stable_under_crlf_text_bodies(tmp_path: Path) -> None:
    lf_root = tmp_path / "lf"
    crlf_root = tmp_path / "crlf"
    lf_root.mkdir()
    crlf_root.mkdir()
    (lf_root / "nested").mkdir()
    (crlf_root / "nested").mkdir()
    (lf_root / "nested" / "note.json").write_bytes(b'{"ok": true}\n')
    (crlf_root / "nested" / "note.json").write_bytes(b'{"ok": true}\r\n')
    (lf_root / "readme.md").write_bytes(b"hello\nworld\n")
    (crlf_root / "readme.md").write_bytes(b"hello\r\nworld\r\n")

    assert canonical_tree_hash(lf_root) == canonical_tree_hash(crlf_root)


def test_canonical_tree_hash_uses_posix_relative_paths(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    (root / "a").mkdir(parents=True)
    (root / "a" / "b.txt").write_text("x\n", encoding="utf-8")
    digest, count = canonical_tree_hash(root)
    assert count == 1
    assert len(digest) == 64
