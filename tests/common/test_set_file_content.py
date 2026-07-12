import codecs
import os
import stat
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


def test_set_file_content_accepts_utf8_alias_for_bom(tmp_path: Path) -> None:
    path = tmp_path / "alias.txt"

    set_file_content(path, "hello", encoding="UTF8", bom=True)

    assert path.read_bytes().startswith(codecs.BOM_UTF8)


def test_set_file_content_accepts_utf8_sig_with_bom(tmp_path: Path) -> None:
    path = tmp_path / "sig.txt"

    set_file_content(path, "hello", encoding="utf-8-sig", bom=True)

    assert path.read_bytes() == codecs.BOM_UTF8 + b"hello"


def test_set_file_content_disables_utf8_sig_bom_when_requested(tmp_path: Path) -> None:
    path = tmp_path / "no-sig.txt"

    set_file_content(path, "hello", encoding="utf-8-sig", bom=False)

    assert path.read_bytes() == b"hello"


def test_set_file_content_rejects_bom_for_non_utf8_codec(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="only supported with UTF-8"):
        set_file_content(tmp_path / "latin1.txt", "hello", encoding="latin-1", bom=True)


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not available on Windows")
def test_set_file_content_atomic_write_preserves_posix_mode(tmp_path: Path) -> None:
    path = tmp_path / "script.sh"
    path.write_text("old", encoding="utf-8")
    path.chmod(0o751)

    set_file_content(path, "new", atomic=True)

    assert stat.S_IMODE(path.stat().st_mode) == 0o751
