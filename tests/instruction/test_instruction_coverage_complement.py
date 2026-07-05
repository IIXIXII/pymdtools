from __future__ import annotations

from pathlib import Path
import re

import pytest

import pymdtools.instruction as instruction


INCLUDE_RE = r"<!--\s*include-file\((?P<name>[\.A-Za-z0-9_/-]+)\)\s*-->"


def test_normalize_read_encoding_accepts_legacy_unknown(monkeypatch, tmp_path: Path):
    source = tmp_path / "snippet.md"
    source.write_text("content", encoding="utf-8")
    calls = {}

    def fake_find_file(filename, start_points, relative_paths, max_up=1):
        return source

    def fake_get_file_content(path, *, encoding=None):
        calls["encoding"] = encoding
        return "content"

    monkeypatch.setattr(instruction.common, "find_file", fake_find_file)
    monkeypatch.setattr(instruction.common, "get_file_content", fake_get_file_content)

    assert instruction.get_file_content_to_include("snippet.md", encoding="UNKNOWN") == "content"
    assert calls["encoding"] is None


def test_get_file_content_to_include_uses_cwd_when_requested(monkeypatch, tmp_path: Path):
    source = tmp_path / "snippet.md"
    source.write_text("content", encoding="utf-8")
    calls = {}

    def fake_find_file(filename, start_points, relative_paths, max_up=1):
        calls["start_points"] = start_points
        return source

    monkeypatch.setattr(instruction.common, "find_file", fake_find_file)

    instruction.get_file_content_to_include("snippet.md", include_cwd=True, encoding="utf-8")

    assert str(Path.cwd()) in calls["start_points"]


def test_get_refs_around_md_file_rejects_invalid_depths():
    with pytest.raises(ValueError, match="depth_up"):
        instruction.get_refs_around_md_file("doc.md", depth_up=-1)
    with pytest.raises(ValueError, match="depth_down"):
        instruction.get_refs_around_md_file("doc.md", depth_down=-2)


def test_get_refs_around_md_file_stops_at_filesystem_root(monkeypatch):
    calls = {}

    def fake_get_refs_from_md_directory(folder, **kwargs):
        calls["folder"] = Path(folder)
        calls["depth"] = kwargs["depth"]
        return {"ok": "OK"}

    monkeypatch.setattr(instruction, "get_refs_from_md_directory", fake_get_refs_from_md_directory)
    root_file = Path(Path.cwd().anchor) / "doc.md"

    assert instruction.get_refs_around_md_file(root_file, depth_up=3, depth_down=0) == {"ok": "OK"}
    assert calls["folder"] == Path(Path.cwd().anchor)
    assert calls["depth"] == 0


def test_search_include_refs_to_md_file_rejects_invalid_depth_down(tmp_path: Path):
    target = tmp_path / "doc.md"
    target.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="depth_down"):
        instruction.search_include_refs_to_md_file(target, depth_down=-2)


def test_get_vars_from_md_text_rejects_non_string():
    with pytest.raises(TypeError, match="text"):
        instruction.get_vars_from_md_text(None)  # type: ignore[arg-type]


def test_escape_var_value_escapes_all_special_characters():
    assert instruction.escape_var_value('a\\b\n\t\r"') == r'a\\b\n\t\r\"'


def test_del_var_to_md_text_rejects_non_string_var_name():
    with pytest.raises(TypeError, match="var_name"):
        instruction.del_var_to_md_text("body", None)  # type: ignore[arg-type]


def test_set_var_to_md_text_rejects_non_string_value():
    with pytest.raises(TypeError, match="var_name and value"):
        instruction.set_var_to_md_text("body", "name", None)  # type: ignore[arg-type]


def test_set_title_in_md_text_rejects_non_string_title():
    with pytest.raises(TypeError, match="new_title"):
        instruction.set_title_in_md_text("body", None)  # type: ignore[arg-type]


def test_set_title_in_md_text_inserts_before_leading_newline():
    assert instruction.set_title_in_md_text("\nBody", "Title").startswith("Title\n=====\n\nBody")


def test_set_title_in_md_text_falls_back_when_stripped_setext_not_in_original(monkeypatch):
    monkeypatch.setattr(instruction, "strip_xml_comment", lambda text: "Ghost\n=====\n")

    out = instruction.set_title_in_md_text("Body\n", "Title", style="preserve")

    assert out.startswith("Title\n=====\n\nBody")


def test_set_title_in_md_text_falls_back_when_stripped_atx_not_in_original(monkeypatch):
    monkeypatch.setattr(instruction, "strip_xml_comment", lambda text: "# Ghost\n")

    out = instruction.set_title_in_md_text("Body\n", "Title", style="preserve")

    assert out.startswith("# Title\n\nBody")


def test_get_vars_around_md_file_stops_at_filesystem_root(monkeypatch):
    calls = {}

    def fake_get_vars_from_md_directory(folder, **kwargs):
        calls["folder"] = Path(folder)
        calls["depth"] = kwargs["depth"]
        return {"ok": "OK"}

    monkeypatch.setattr(instruction, "get_vars_from_md_directory", fake_get_vars_from_md_directory)
    root_file = Path(Path.cwd().anchor) / "doc.md"

    assert instruction.get_vars_around_md_file(root_file, depth_up=3, depth_down=0) == {"ok": "OK"}
    assert calls["folder"] == Path(Path.cwd().anchor)
    assert calls["depth"] == 0


def test_get_vars_around_md_file_increases_positive_depth(monkeypatch, tmp_path: Path):
    calls = {}
    target = tmp_path / "a" / "b" / "doc.md"
    target.parent.mkdir(parents=True)
    target.write_text("", encoding="utf-8")

    def fake_get_vars_from_md_directory(folder, **kwargs):
        calls["depth"] = kwargs["depth"]
        return {}

    monkeypatch.setattr(instruction, "get_vars_from_md_directory", fake_get_vars_from_md_directory)

    instruction.get_vars_around_md_file(target, depth_up=2, depth_down=1)

    assert calls["depth"] == 3


def test_get_vars_around_md_file_keeps_zero_depth_when_moving_up(monkeypatch, tmp_path: Path):
    calls = {}
    target = tmp_path / "sub" / "doc.md"
    target.parent.mkdir(parents=True)
    target.write_text("", encoding="utf-8")

    def fake_get_vars_from_md_directory(folder, **kwargs):
        calls["depth"] = kwargs["depth"]
        return {}

    monkeypatch.setattr(instruction, "get_vars_from_md_directory", fake_get_vars_from_md_directory)

    instruction.get_vars_around_md_file(target, depth_up=1, depth_down=0)

    assert calls["depth"] == 0


def test_include_files_to_md_text_accepts_string_regex(monkeypatch):
    monkeypatch.setattr(instruction, "get_file_content_to_include", lambda name, **kwargs: "content")

    out = instruction.include_files_to_md_text(
        "<!-- include-file(a.md) -->",
        include_file_re=INCLUDE_RE,
        render_mode="raw",
    )

    assert out == "content"


def test_ensure_include_file_rejects_non_string_text():
    with pytest.raises(TypeError, match="text"):
        instruction.ensure_include_file_in_md_text(None, "a.md")  # type: ignore[arg-type]


def test_ensure_include_file_rejects_non_string_filename():
    with pytest.raises(ValueError, match="filename"):
        instruction.ensure_include_file_in_md_text("body", None)  # type: ignore[arg-type]


def test_ensure_include_file_with_leading_newline_when_missing():
    out = instruction.ensure_include_file_in_md_text("\nBody", "a.md")
    assert out == "<!-- include-file(a.md) -->\n\n\nBody"


def test_ensure_include_file_adds_blank_line_before_following_content():
    out = instruction.ensure_include_file_in_md_text(
        "<!-- include-file(a.md) -->Body",
        "b.md",
    )

    assert out == "<!-- include-file(a.md) -->\n<!-- include-file(b.md) -->\n\nBody"


def test_ensure_include_file_preserves_existing_trailing_newline_from_match():
    include_re_with_newline = re.compile(
        r"<!--\s*include-file\((?P<name>[\.A-Za-z0-9_/-]+)\)\s*-->\n"
    )

    out = instruction.ensure_include_file_in_md_text(
        "<!-- include-file(a.md) -->\nBody",
        "b.md",
        include_file_re=include_re_with_newline,
    )

    assert out == "<!-- include-file(a.md) -->\n<!-- include-file(b.md) -->\n\nBody"


def test_get_include_file_list_accepts_string_regex():
    text = "<!-- include-file(a.md) --><!-- include-file(a.md) -->"

    assert instruction.get_include_file_list(text, include_file_re=INCLUDE_RE, unique=True) == ["a.md"]


def test_del_include_file_to_md_text_rejects_invalid_inputs():
    with pytest.raises(TypeError, match="text"):
        instruction.del_include_file_to_md_text(None, "a.md")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="filename"):
        instruction.del_include_file_to_md_text("body", "")


def test_del_include_file_to_md_text_accepts_string_regex():
    text = "A<!-- include-file(a.md) -->B"

    assert instruction.del_include_file_to_md_text(text, "a.md", include_file_re=INCLUDE_RE) == "AB"
