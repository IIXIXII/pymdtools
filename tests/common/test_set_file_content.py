import codecs
from pathlib import Path

import pytest

from pymdtools.common import set_file_content, get_file_content


def test_set_file_content_creates_file(tmp_path):
    f = tmp_path / "a.txt"
    out = set_file_content(f, "hello", encoding="utf-8", bom=False)
    assert Path(out).exists()
    assert Path(out).read_text(encoding="utf-8") == "hello"


def test_set_file_content_writes_utf8_bom_when_enabled(tmp_path):
    f = tmp_path / "bom.txt"
    set_file_content(f, "hello", encoding="utf-8", bom=True, atomic=False)
    data = f.read_bytes()
    assert data.startswith(codecs.BOM_UTF8)


def test_set_file_content_does_not_write_bom_when_disabled(tmp_path):
    f = tmp_path / "nobom.txt"
    set_file_content(f, "hello", encoding="utf-8", bom=False, atomic=False)
    data = f.read_bytes()
    assert not data.startswith(codecs.BOM_UTF8)


def test_set_file_content_overwrites_existing(tmp_path):
    f = tmp_path / "a.txt"
    set_file_content(f, "v1", encoding="utf-8", bom=False)
    set_file_content(f, "v2", encoding="utf-8", bom=False)
    assert f.read_text(encoding="utf-8") == "v2"


def test_set_file_content_atomic_write(tmp_path):
    f = tmp_path / "atomic.txt"
    set_file_content(f, "hello", encoding="utf-8", bom=False, atomic=True)
    assert f.read_text(encoding="utf-8") == "hello"


def test_set_file_content_creates_parent_dirs(tmp_path):
    f = tmp_path / "a" / "b" / "c.txt"
    set_file_content(f, "x", encoding="utf-8", bom=False)
    assert f.exists()


def test_roundtrip_with_get_file_content_bom(tmp_path):
    f = tmp_path / "roundtrip.txt"
    set_file_content(f, "hello", encoding="utf-8", bom=True)
    assert get_file_content(f, encoding="utf-8") == "hello"


def test_set_file_content_rejects_non_str_content(tmp_path):
    f = tmp_path / "a.txt"
    with pytest.raises(TypeError):
        set_file_content(f, b"nope")  # type: ignore[arg-type]
