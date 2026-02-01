import pytest

from pymdtools.common import detect_file_encoding


def test_detect_file_encoding_utf8(tmp_path):
    f = tmp_path / "utf8.txt"
    f.write_text("éàç — test", encoding="utf-8")

    enc = detect_file_encoding(f, min_confidence=0.1)
    # chardet renvoie souvent 'utf-8' pour ce cas
    assert "utf" in enc


def test_detect_file_encoding_ascii(tmp_path):
    f = tmp_path / "ascii.txt"
    f.write_text("simple ascii text", encoding="ascii")

    enc = detect_file_encoding(f, min_confidence=0.1)
    # peut retourner 'ascii' ou 'utf-8'
    assert enc in {"ascii", "utf-8"}


def test_detect_file_encoding_empty_file_returns_default(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")

    assert detect_file_encoding(f, default="utf-8") == "utf-8"


def test_detect_file_encoding_low_confidence_returns_default(tmp_path):
    f = tmp_path / "small.txt"
    f.write_bytes(b"\xff")  # trop faible / ambigu

    enc = detect_file_encoding(f, default="utf-8", min_confidence=0.99)
    assert enc == "utf-8"


def test_detect_file_encoding_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        detect_file_encoding(tmp_path / "missing.txt")


def test_detect_file_encoding_directory_raises(tmp_path):
    with pytest.raises(IsADirectoryError):
        detect_file_encoding(tmp_path)
