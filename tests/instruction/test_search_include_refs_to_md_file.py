from __future__ import annotations

from pathlib import Path
import pytest

from pymdtools.instruction import search_include_refs_to_md_file
from pymdtools.instruction import _INCLUDE_FILE_RE

def test_include_file_name_supports_slash():
    text = '<!-- include-file(templates/header.md) x -->'
    assert _INCLUDE_FILE_RE.search(text)

def _write(p: Path, name: str, content: str) -> Path:
    f = p / name
    f.write_text(content, encoding="utf-8")
    return f


def test_search_include_refs_to_md_file_applies_refs_found_around(tmp_path: Path):
    # root/
    #   refs.md (defines ref x)
    #   sub/
    #     target.md (includes x)
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)

    _write(root, "refs.md", "<!-- begin-ref(x) -->XVAL<!-- end-ref -->")
    target = _write(
        sub,
        "target.md",
        "A\n<!-- begin-include(x) -->OLD<!-- end-include -->\nB\n",
    )

    search_include_refs_to_md_file(
        target,
        backup_option=False,
        filename_ext=".md",
        depth_up=1,
        depth_down=1,
    )

    out = target.read_text(encoding="utf-8").lstrip("\ufeff")
    assert "XVAL" in out
    assert "OLD" not in out


def test_search_include_refs_to_md_file_creates_backup(tmp_path: Path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()

    _write(root, "refs.md", "<!-- begin-ref(x) -->XVAL<!-- end-ref -->")
    target = _write(
        root,
        "target.md",
        "<!-- begin-include(x) -->OLD<!-- end-include -->",
    )

    # deterministic backup naming
    import pymdtools.common as common
    monkeypatch.setattr(common, "today_utc", lambda: "2026-02-01")

    search_include_refs_to_md_file(
        target,
        backup_option=True,
        backup_ext=".bak",
        filename_ext=".md",
        depth_up=0,
        depth_down=0,
    )

    backups = list(root.glob("target.md.2026-02-01-*.bak"))
    assert len(backups) == 1


def test_search_include_refs_to_md_file_raises_on_invalid_depth(tmp_path: Path):
    p = tmp_path / "a.md"
    p.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError):
        search_include_refs_to_md_file(p, depth_up=-1)
