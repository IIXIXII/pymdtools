from __future__ import annotations

from pathlib import Path
import pytest

import pymdtools.instruction as instruction


def test_get_file_content_to_include_calls_search_and_reads(monkeypatch, tmp_path: Path):
    calls = {}

    def fake_search_for_file(file_wanted, start_points, relative_paths, nb_up_path=1):
        calls["file_wanted"] = file_wanted
        calls["start_points"] = start_points
        calls["relative_paths"] = relative_paths
        calls["nb_up_path"] = nb_up_path
        return str(tmp_path / "found.md")

    def fake_get_file_content(filename, encoding="UNKNOWN"):
        calls["read_filename"] = filename
        calls["encoding"] = encoding
        return "OK"

    monkeypatch.setattr(instruction.common, "search_for_file", fake_search_for_file)
    monkeypatch.setattr(instruction.common, "get_file_content", fake_get_file_content)

    out = instruction.get_file_content_to_include(
        "snippet.md",
        search_folders=[tmp_path],
        include_cwd=False,
        encoding="utf-8",
    )

    assert out == "OK"
    assert calls["file_wanted"] == "snippet.md"
    assert calls["nb_up_path"] == 1
    assert calls["encoding"] == "utf-8"
    assert calls["read_filename"].endswith("found.md")


def test_get_file_content_to_include_rejects_absolute_path():
    with pytest.raises(ValueError):
        instruction.get_file_content_to_include("/etc/passwd", include_cwd=False)


def test_get_file_content_to_include_rejects_parent_traversal():
    with pytest.raises(ValueError):
        instruction.get_file_content_to_include("../secret.md", include_cwd=False)
