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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_text(p: Path, text: str, encoding: str = "utf-8") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding=encoding)


def _write_bytes(p: Path, data: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


# ---------------------------------------------------------------------------
# Basic behavior
# ---------------------------------------------------------------------------

def test_empty_file_is_not_binary(tmp_path: Path) -> None:
    p = tmp_path / "empty.txt"
    _write_bytes(p, b"")

    assert is_binary_file(p) is False


def test_utf8_text_file_is_not_binary(tmp_path: Path) -> None:
    p = tmp_path / "text.txt"
    _write_text(p, "Hello world äöü €")

    assert is_binary_file(p) is False


def test_utf8_bom_file_is_not_binary(tmp_path: Path) -> None:
    p = tmp_path / "utf8_bom.txt"
    # UTF-8 BOM
    _write_bytes(p, b"\xef\xbb\xbfHello")

    assert is_binary_file(p) is False


def test_utf16_le_bom_file_is_not_binary(tmp_path: Path) -> None:
    p = tmp_path / "utf16le.txt"
    # UTF-16 LE BOM + valid UTF-16 content
    _write_bytes(p, b"\xff\xfeH\x00i\x00")

    assert is_binary_file(p) is False


def test_file_with_null_byte_is_binary(tmp_path: Path) -> None:
    p = tmp_path / "null.bin"
    _write_bytes(p, b"abc\x00def")

    assert is_binary_file(p) is True


def test_random_binary_file_is_binary(tmp_path: Path) -> None:
    p = tmp_path / "random.bin"
    _write_bytes(p, bytes(range(256)))  # contains null byte

    assert is_binary_file(p) is True


# ---------------------------------------------------------------------------
# sample_size behavior
# ---------------------------------------------------------------------------

def test_binary_detection_with_small_sample_size(tmp_path: Path) -> None:
    p = tmp_path / "late_null.bin"

    # Null byte appears after 10 bytes
    _write_bytes(p, b"A" * 10 + b"\x00" + b"B" * 100)

    # If sample_size too small, may not see null byte
    assert is_binary_file(p, sample_size=5) is False

    # Larger sample detects null byte
    assert is_binary_file(p, sample_size=20) is True


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_is_binary_file_raises_if_missing(tmp_path: Path) -> None:
    p = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        is_binary_file(p)


def test_is_binary_file_raises_if_directory(tmp_path: Path) -> None:
    d = tmp_path / "dir"
    d.mkdir()

    with pytest.raises(IsADirectoryError):
        is_binary_file(d)