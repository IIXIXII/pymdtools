"""Filesystem contracts for includes, including explicit parent access."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pymdtools.instruction import get_file_content_to_include, include_files_to_md_text


def test_parent_search_requires_explicit_permission(tmp_path: Path) -> None:
    nested = tmp_path / "docs" / "chapters"
    nested.mkdir(parents=True)
    (tmp_path / "parent-contract.md").write_text("caf\u00e9", encoding="cp1252")
    for depth in (0, 1):
        with pytest.raises(FileNotFoundError):
            get_file_content_to_include(
                "parent-contract.md", search_folders=[nested], nb_up_path=depth
            )
    assert (
        get_file_content_to_include(
            "parent-contract.md", search_folders=[nested], nb_up_path=2, encoding="cp1252"
        )
        == "caf\u00e9"
    )


def test_nearest_include_wins_over_parent(tmp_path: Path) -> None:
    nested = tmp_path / "docs"
    nested.mkdir()
    (tmp_path / "precedence-contract.md").write_text("parent", encoding="utf-8")
    (nested / "precedence-contract.md").write_text("local", encoding="utf-8")
    assert (
        get_file_content_to_include("precedence-contract.md", search_folders=[nested], nb_up_path=1)
        == "local"
    )


def test_parent_permission_does_not_allow_symlink_escape(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    nested = allowed / "docs"
    nested.mkdir(parents=True)
    outside = tmp_path / "private.md"
    outside.write_text("private", encoding="utf-8")
    try:
        (allowed / "escape-contract.md").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    # The filesystem search rejects the escape before the include-level check.
    with pytest.raises(ValueError, match="escapes its anchor"):
        get_file_content_to_include("escape-contract.md", search_folders=[nested], nb_up_path=1)


@settings(max_examples=40, deadline=None)
@given(st.text(alphabet="abc XYZ\u00e9\u03a9\u4e2d0123*_[]()\n\t", min_size=1, max_size=200))
def test_raw_include_preserves_unicode_content_and_surrounding_text(content: str) -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "unicode-contract.md").write_text(content, encoding="utf-8", newline="\n")
        result = include_files_to_md_text(
            "before\n<!-- include-file(unicode-contract.md) -->\nafter",
            render_mode="raw",
            search_folders=[root],
            encoding="utf-8",
        )
        assert result == "before\n" + content + "\nafter"
