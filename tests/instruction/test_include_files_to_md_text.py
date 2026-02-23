from __future__ import annotations

import pytest

import pymdtools.instruction as instruction


def test_include_files_to_md_text_replaces_with_box(monkeypatch):
    monkeypatch.setattr(instruction, "get_file_content_to_include", lambda name, **kw: "L1\nL2\n")

    text = "A\n<!-- include-file(x.md) -->\nB\n"
    out = instruction.include_files_to_md_text(text, render_mode="box")

    assert "include-file(x.md)" in out
    assert "| L1" in out
    assert "| L2" in out
    assert "A\n" in out and "\nB\n" in out


def test_include_files_to_md_text_replaces_with_raw(monkeypatch):
    monkeypatch.setattr(instruction, "get_file_content_to_include", lambda name, **kw: "CONTENT\n")

    text = "A\n<!-- include-file(x.md) -->\nB\n"
    out = instruction.include_files_to_md_text(text, render_mode="raw")

    assert "CONTENT\n" in out
    assert "include-file(x.md)" not in out  # directive removed in raw mode


def test_include_files_to_md_text_keeps_directive_if_missing_and_not_error(monkeypatch):
    def _raise(*args, **kwargs):
        raise FileNotFoundError("nope")

    monkeypatch.setattr(instruction, "get_file_content_to_include", _raise)

    text = "A\n<!-- include-file(x.md) -->\nB\n"
    out = instruction.include_files_to_md_text(text, error_if_no_file=False)

    assert "<!-- include-file(x.md) -->" in out


def test_include_files_to_md_text_raises_if_missing_by_default(monkeypatch):
    def _raise(*args, **kwargs):
        raise FileNotFoundError("nope")

    monkeypatch.setattr(instruction, "get_file_content_to_include", _raise)

    text = "<!-- include-file(x.md) -->"
    with pytest.raises(FileNotFoundError):
        instruction.include_files_to_md_text(text, error_if_no_file=True)


def test_include_files_to_md_text_multiple_includes(monkeypatch):
    monkeypatch.setattr(instruction, "get_file_content_to_include", lambda name, **kw: f"{name}\n")

    text = "<!-- include-file(a.md) --><!-- include-file(b.md) -->"
    out = instruction.include_files_to_md_text(text, render_mode="raw")

    assert "a.md\n" in out
    assert "b.md\n" in out