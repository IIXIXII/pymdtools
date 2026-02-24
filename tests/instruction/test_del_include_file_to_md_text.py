from __future__ import annotations

import re
import pymdtools.instruction as instruction


INCLUDE_RE = re.compile(r"<!--\s*include-file\((?P<name>[\.A-Za-z0-9_/-]+)\)\s*-->")


def test_del_include_file_removes_matching():
    text = "A<!-- include-file(a.md) -->B"
    out = instruction.del_include_file_to_md_text(text, "a.md", include_file_re=INCLUDE_RE)
    assert "<!-- include-file(a.md) -->" not in out
    assert out == "AB"


def test_del_include_file_keeps_other_files():
    text = "A<!-- include-file(a.md) --><!-- include-file(b.md) -->B"
    out = instruction.del_include_file_to_md_text(text, "a.md", include_file_re=INCLUDE_RE)
    assert "include-file(a.md)" not in out
    assert "include-file(b.md)" in out


def test_del_include_file_removes_all_by_default():
    text = "<!-- include-file(a.md) --><!-- include-file(a.md) -->"
    out = instruction.del_include_file_to_md_text(text, "a.md", include_file_re=INCLUDE_RE)
    assert "include-file(a.md)" not in out


def test_del_include_file_first_only():
    text = "<!-- include-file(a.md) --><!-- include-file(a.md) -->"
    out = instruction.del_include_file_to_md_text(text, "a.md", include_file_re=INCLUDE_RE, first_only=True)
    assert out.count("include-file(a.md)") == 1


def test_del_include_file_supports_slash_name():
    text = "<!-- include-file(dir/a.md) -->"
    out = instruction.del_include_file_to_md_text(text, "dir/a.md", include_file_re=INCLUDE_RE)
    assert "include-file(dir/a.md)" not in out