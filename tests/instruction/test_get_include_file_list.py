from __future__ import annotations

import re
import pymdtools.instruction as instruction


INCLUDE_RE = re.compile(r"<!--\s*include-file\((?P<name>[\.A-Za-z0-9_/-]+)\)\s*-->")


def test_get_include_file_list_empty():
    assert instruction.get_include_file_list("no directives", include_file_re=INCLUDE_RE) == []


def test_get_include_file_list_ordered():
    text = "<!-- include-file(a.md) --><!-- include-file(b.md) -->"
    assert instruction.get_include_file_list(text, include_file_re=INCLUDE_RE) == ["a.md", "b.md"]


def test_get_include_file_list_duplicates_kept_by_default():
    text = "<!-- include-file(a.md) --><!-- include-file(a.md) -->"
    assert instruction.get_include_file_list(text, include_file_re=INCLUDE_RE) == ["a.md", "a.md"]


def test_get_include_file_list_unique():
    text = "<!-- include-file(a.md) --><!-- include-file(a.md) --><!-- include-file(b.md) -->"
    assert instruction.get_include_file_list(text, include_file_re=INCLUDE_RE, unique=True) == ["a.md", "b.md"]


def test_get_include_file_list_supports_slash():
    text = "<!-- include-file(dir/a.md) -->"
    assert instruction.get_include_file_list(text, include_file_re=INCLUDE_RE) == ["dir/a.md"]