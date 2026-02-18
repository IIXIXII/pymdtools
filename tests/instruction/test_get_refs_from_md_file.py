from __future__ import annotations

from pathlib import Path
import pytest

from pymdtools.instruction import get_refs_from_md_file


def test_get_refs_from_md_file_extracts_refs(tmp_path: Path):
    p = tmp_path / "a.md"
    p.write_text(
        "before\n"
        "<!-- begin-ref(x) -->\n"
        "X\n"
        "<!-- end-ref -->\n"
        "after\n",
        encoding="utf-8",
    )

    out = get_refs_from_md_file(p)
    assert out == {"x": "\nX\n"}


def test_get_refs_from_md_file_raises_on_wrong_extension(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("<!-- begin-ref(x) -->X<!-- end-ref -->", encoding="utf-8")

    with pytest.raises(Exception):
        get_refs_from_md_file(p, filename_ext=".md")


def test_get_refs_from_md_file_raises_on_missing_file(tmp_path: Path):
    p = tmp_path / "missing.md"
    with pytest.raises(Exception):
        get_refs_from_md_file(p)
