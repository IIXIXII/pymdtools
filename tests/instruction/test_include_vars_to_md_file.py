from __future__ import annotations

from pathlib import Path
import pytest

from pymdtools.instruction import include_vars_to_md_file


def test_include_vars_to_md_file_rewrites_file(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text(
        "A\n<!-- begin-var(x) -->OLD<!-- end-var -->\nB\n",
        encoding="utf-8",
    )

    include_vars_to_md_file(f, {"x": "NEW"}, backup_option=False, filename_ext=".md")

    out = f.read_text(encoding="utf-8").lstrip("\ufeff")
    assert "NEW" in out
    assert "OLD" not in out


def test_include_vars_to_md_file_unknown_var_raises(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text("<!-- begin-var(x) -->OLD<!-- end-var -->", encoding="utf-8")

    with pytest.raises(KeyError):
        include_vars_to_md_file(
            f, {}, backup_option=False, error_if_var_not_found=True
        )


def test_include_vars_to_md_file_unknown_var_can_be_ignored(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text(
        "<!-- begin-var(x) -->X<!-- end-var -->\n"
        "<!-- begin-var(y) -->Y<!-- end-var -->\n",
        encoding="utf-8",
    )

    include_vars_to_md_file(
        f, {"y": "YY"}, backup_option=False, error_if_var_not_found=False
    )

    out = f.read_text(encoding="utf-8").lstrip("\ufeff")
    assert "X" in out
    assert "YY" in out
    assert "Y" not in out


def test_include_vars_to_md_file_creates_backup(tmp_path: Path, monkeypatch):
    f = tmp_path / "doc.md"
    f.write_text("<!-- begin-var(x) -->OLD<!-- end-var -->", encoding="utf-8")

    # deterministic backup naming if your common.create_backup uses get_today()
    import pymdtools.common as common
    monkeypatch.setattr(common, "get_today", lambda: "2026-02-01")

    include_vars_to_md_file(f, {"x": "NEW"}, backup_option=True)

    backups = list(tmp_path.glob("doc.md.2026-02-01-*.bak"))
    # If your backup scheme differs, adapt this assertion accordingly.
    assert len(backups) >= 1
