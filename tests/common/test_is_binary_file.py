import codecs
import pytest
from pathlib import Path

from pymdtools.common import is_binary_file


def test_is_binary_file_text_ascii(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello world", encoding="ascii")
    assert is_binary_file(f) is False


def test_is_binary_file_text_utf8(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("éàç", encoding="utf-8")
    assert is_binary_file(f) is False


def test_is_binary_file_empty_file(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")
    assert is_binary_file(f) is False


def test_is_binary_file_binary_with_null_bytes(tmp_path):
    f = tmp_path / "bin.dat"
    f.write_bytes(b"\x00\x01\x02\x03")
    assert is_binary_file(f) is True


def test_is_binary_file_utf16_with_bom(tmp_path):
    f = tmp_path / "utf16.txt"
    f.write_bytes(codecs.BOM_UTF16_LE + "abc".encode("utf-16-le"))
    assert is_binary_file(f) is False


def test_is_binary_file_raises_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        is_binary_file(tmp_path / "missing")


def test_is_binary_file_raises_if_directory(tmp_path):
    with pytest.raises(IsADirectoryError):
        is_binary_file(tmp_path)
