from __future__ import annotations

from pathlib import Path
import pytest

from pymdtools.instruction import include_refs_to_md_file


def test_include_refs_to_md_file_rewrites_file(tmp_path: Path):
    p = tmp_path / "doc.md"
    p.write_text(
        "A\n<!-- begin-include(x) -->\nOLD\n<!-- end-include -->\nB\n",
        encoding="utf-8",
    )

    include_refs_to_md_file(p, {"x": "NEW\n"}, backup_option=False)

    out = p.read_text(encoding="utf-8").lstrip("\ufeff")
    assert "NEW\n" in out
    assert "OLD" not in out
    assert "<!-- begin-include(x) -->" in out
    assert "<!-- end-include -->" in out


def test_include_refs_to_md_file_creates_backup(tmp_path: Path, monkeypatch):
    p = tmp_path / "doc.md"
    p.write_text("<!-- begin-include(x) -->OLD<!-- end-include -->", encoding="utf-8")

    # Make backup name deterministic
    import pymdtools.common as common
    monkeypatch.setattr(common, "today_utc", lambda: "2026-02-01")

    include_refs_to_md_file(p, {"x": "NEW"}, backup_option=True, backup_ext=".bak")

    backups = list(tmp_path.glob("doc.md.2026-02-01-*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8").lstrip("\ufeff")  # backup exists and readable


def test_include_refs_to_md_file_unknown_key_raises(tmp_path: Path):
    p = tmp_path / "doc.md"
    p.write_text("<!-- begin-include(x) -->X<!-- end-include -->", encoding="utf-8")

    with pytest.raises(KeyError):
        include_refs_to_md_file(p, {}, backup_option=False, error_if_no_key=True)


def test_include_refs_to_md_file_unknown_key_can_be_ignored(tmp_path: Path):
    p = tmp_path / "doc.md"
    p.write_text(
        "<!-- begin-include(x) -->X<!-- end-include -->\n"
        "<!-- begin-include(y) -->Y<!-- end-include -->\n",
        encoding="utf-8",
    )

    include_refs_to_md_file(
        p,
        {"y": "YY"},
        backup_option=False,
        error_if_no_key=False,
    )

    out = p.read_text(encoding="utf-8").lstrip("\ufeff")
    assert "X" in out   # unchanged
    assert "YY" in out  # replaced
    assert "Y" not in out
