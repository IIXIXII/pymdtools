import codecs
import pytest
from pathlib import Path

from pymdtools.common import get_file_content


def test_get_file_content_reads_utf8(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello", encoding="utf-8")
    assert get_file_content(f, encoding="utf-8") == "hello"


def test_get_file_content_strips_utf8_bom(tmp_path):
    f = tmp_path / "bom.txt"
    f.write_bytes(codecs.BOM_UTF8 + "hello".encode("utf-8"))

    # encoding utf-8 -> utf-8-sig removes BOM transparently
    assert get_file_content(f, encoding="utf-8") == "hello"


def test_get_file_content_defensive_strips_unicode_bom_char(tmp_path):
    f = tmp_path / "weird.txt"
    f.write_text("\ufeffhello", encoding="utf-8")
    assert get_file_content(f, encoding="utf-8") == "hello"


def test_get_file_content_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        get_file_content(tmp_path / "missing.txt")


def test_get_file_content_raises_for_directory(tmp_path):
    with pytest.raises(IsADirectoryError):
        get_file_content(tmp_path)


def test_get_file_content_raises_unicode_decode_error(tmp_path):
    f = tmp_path / "bad.txt"
    # bytes invalid for utf-8
    f.write_bytes(b"\xff\xfe\xfa")

    with pytest.raises(UnicodeDecodeError):
        get_file_content(f, encoding="utf-8")


@pytest.mark.parametrize(
    ("encoding", "text"),
    [
        ("cp1252", "Café — 10 €"),
        ("latin-1", "Déjà vu"),
    ],
)
def test_get_file_content_reads_explicit_single_byte_text(
    tmp_path: Path,
    encoding: str,
    text: str,
) -> None:
    path = tmp_path / f"{encoding}.txt"
    path.write_bytes(text.encode(encoding))

    assert get_file_content(path, encoding=encoding) == text


def test_get_file_content_reads_utf16_without_bom_when_explicit(tmp_path: Path) -> None:
    path = tmp_path / "utf16.txt"
    path.write_bytes("hello".encode("utf-16-le"))

    assert get_file_content(path, encoding="utf-16-le") == "hello"
