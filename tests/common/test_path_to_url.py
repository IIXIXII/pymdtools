from pathlib import Path

from pymdtools.common import path_to_url


def test_path_to_url_basic():
    assert path_to_url("A Folder/File.txt") == "a-folder/file.txt"


def test_path_to_url_unicode_removed():
    assert path_to_url("Été/Mon fichier.txt") == "ete/mon-fichier.txt"


def test_path_to_url_unicode_kept_when_disabled():
    assert path_to_url("Été/Mon fichier.txt", remove_accent=False) == "%C3%A9t%C3%A9/mon-fichier.txt"


def test_path_to_url_windows_path():
    p = Path(r"C:\My Folder\Sub Dir\File.md")
    assert path_to_url(p).endswith("c%3A/my-folder/sub-dir/file.md")


def test_path_to_url_preserves_slashes():
    assert path_to_url("a / b / c") == "a/b/c"
