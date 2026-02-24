from __future__ import annotations

import re
import pytest

import pymdtools.instruction as instruction


# Simple, strict regex for the tests; your module can use its own pattern
INCLUDE_RE = re.compile(r"<!--\s*include-file\((?P<name>[\.A-Za-z0-9_/-]+)\)\s*-->")

def test_ensure_adds_when_missing():
    text = "Body\n"
    out = instruction.ensure_include_file_in_md_text(text, "a.md", include_file_re=INCLUDE_RE)
    assert "<!-- include-file(a.md) -->" in out


def test_ensure_does_not_duplicate():
    text = "<!-- include-file(a.md) -->\n\nBody\n"
    out = instruction.ensure_include_file_in_md_text(text, "a.md", include_file_re=INCLUDE_RE)
    assert out.count("include-file(a.md)") == 1


def test_ensure_appends_after_last_include():
    text = (
        "<!-- include-file(a.md) -->\n"
        "<!-- include-file(b.md) -->\n"
        "\nBody\n"
    )
    out = instruction.ensure_include_file_in_md_text(text, "c.md", include_file_re=INCLUDE_RE)

    # c.md should appear after b.md
    assert out.find("include-file(b.md)") < out.find("include-file(c.md)")


def test_ensure_supports_slash_name():
    text = "Body\n"
    out = instruction.ensure_include_file_in_md_text(text, "dir/a.md", include_file_re=INCLUDE_RE)
    assert "include-file(dir/a.md)" in out


def test_ensure_rejects_blank_filename():
    with pytest.raises(ValueError):
        instruction.ensure_include_file_in_md_text("x", "   ", include_file_re=INCLUDE_RE)