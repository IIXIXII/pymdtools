from __future__ import annotations

from pathlib import Path
import pytest

from pymdtools.instruction import get_vars_from_md_file


def test_get_vars_from_md_file_reads_and_parses(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text(r'<!-- var(a)="he said \"hi\"\nline2" -->', encoding="utf-8")

    out = get_vars_from_md_file(f, filename_ext=".md", encoding="utf-8")
    assert out["a"] == 'he said "hi"\nline2'


def test_get_vars_from_md_file_extends_previous_vars(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text(r'<!-- var(b)="2" -->', encoding="utf-8")

    out = get_vars_from_md_file(f, previous_vars={"a": "1"}, encoding="utf-8")
    assert out == {"a": "1", "b": "2"}


def test_get_vars_from_md_file_duplicate_raises(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text(r'<!-- var(a)="1" --><!-- var(a)="2" -->', encoding="utf-8")

    with pytest.raises(ValueError):
        get_vars_from_md_file(f, encoding="utf-8")
