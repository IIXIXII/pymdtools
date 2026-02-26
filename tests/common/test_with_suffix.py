import pytest

from pymdtools.common import with_suffix


def test_with_suffix_replaces_existing_extension():
    assert str(with_suffix("file.txt", ".md")) == "file.md"


def test_with_suffix_adds_extension_if_missing():
    assert str(with_suffix("file", ".md")) == "file.md"


def test_with_suffix_on_path():
    out = str(with_suffix("/tmp/file.txt", ".pdf")).replace("\\", "/")
    assert out.endswith("/tmp/file.pdf")
