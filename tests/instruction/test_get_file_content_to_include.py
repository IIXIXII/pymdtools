from __future__ import annotations

from pathlib import Path
import pytest

import pymdtools.instruction as instruction


def test_get_file_content_to_include_calls_search_and_reads(monkeypatch, tmp_path: Path):
    calls = {}

    def fake_find_file(file_wanted, start_points, relative_paths, max_up=1):
        calls["file_wanted"] = file_wanted
        calls["start_points"] = start_points
        calls["relative_paths"] = relative_paths
        calls["max_up"] = max_up
        return str(tmp_path / "found.md")

    def fake_get_file_content(filename, encoding="UNKNOWN"):
        calls["read_filename"] = filename
        calls["encoding"] = encoding
        return "OK"

    monkeypatch.setattr(instruction.common, "find_file", fake_find_file)
    monkeypatch.setattr(instruction.common, "get_file_content", fake_get_file_content)

    out = instruction.get_file_content_to_include(
        "snippet.md",
        search_folders=[tmp_path],
        include_cwd=False,
        encoding="utf-8",
    )

    assert out == "OK"
    assert calls["file_wanted"] == "snippet.md"
    assert calls["max_up"] == 0
    assert calls["encoding"] == "utf-8"
    assert Path(calls["read_filename"]).name == "found.md"


def test_get_file_content_to_include_rejects_absolute_path():
    with pytest.raises(ValueError):
        instruction.get_file_content_to_include("/etc/passwd", include_cwd=False)


def test_get_file_content_to_include_rejects_parent_traversal():
    with pytest.raises(ValueError):
        instruction.get_file_content_to_include("../secret.md", include_cwd=False)


def test_get_file_content_to_include_rejects_drive_relative_path():
    with pytest.raises(ValueError):
        instruction.get_file_content_to_include("C:secret.md", include_cwd=False)
