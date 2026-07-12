from __future__ import annotations

from pathlib import Path

import pytest

import pymdtools.instruction as instruction


def test_titles_ignore_fenced_code_and_follow_document_order() -> None:
    text = "```markdown\n# Fake\n```\n# First\n\nLater\n=====\n"

    assert instruction.get_title_from_md_text(text) == "First"

    out = instruction.set_title_in_md_text(text, "New", style="preserve")

    assert "```markdown\n# Fake\n```" in out
    assert "# New\n" in out
    assert "Later\n=====\n" in out


def test_directive_discovery_ignores_all_markdown_code_forms() -> None:
    text = (
        "`<!-- var(hidden)=\"inline\" -->`\n"
        "```markdown\n"
        "<!-- var(hidden)=\"fenced\" -->\n"
        "<!-- begin-ref(hidden) -->NO<!-- end-ref -->\n"
        "<!-- begin-include(hidden) -->OLD<!-- end-include -->\n"
        "```\n"
        "    <!-- var(hidden)=\"indented\" -->\n"
        "\n"
        "\t<!-- begin-include(hidden) -->OLD<!-- end-include -->\n"
        "<!-- var(real)=\"yes\" -->\n"
        "<!-- begin-ref(real) -->YES<!-- end-ref -->\n"
        "<!-- begin-include(real) -->OLD<!-- end-include -->\n"
    )

    assert instruction.get_vars_from_md_text(text) == {"real": "yes"}
    assert instruction.get_refs_from_md_text(text) == {"real": "YES"}
    assert instruction.refs_in_md_text(text) == ["real"]


def test_include_file_ignores_code_spans_and_fences(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_include(name: str, **kwargs: object) -> str:
        del kwargs
        calls.append(name)
        return "INCLUDED"

    monkeypatch.setattr(instruction, "get_file_content_to_include", fake_include)
    text = (
        "`<!-- include-file(inline.md) -->`\n"
        "```\n<!-- include-file(fenced.md) -->\n```\n"
        "    <!-- include-file(indented.md) -->\n"
        "<!-- include-file(real.md) -->\n"
    )

    out = instruction.include_files_to_md_text(text, render_mode="raw")

    assert calls == ["real.md"]
    assert "include-file(inline.md)" in out
    assert "include-file(fenced.md)" in out
    assert "include-file(indented.md)" in out
    assert out.endswith("INCLUDED\n")


def test_include_references_handles_many_blocks_without_recursion() -> None:
    block = "<!-- begin-include(key) -->OLD<!-- end-include -->"
    text = "\n".join(block for _ in range(1_100))

    out = instruction.include_refs_to_md_text(text, {"key": "NEW"})

    assert out.count("NEW") == 1_100
    assert "OLD" not in out


def test_include_resolution_rejects_result_outside_allowed_roots(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside" / "secret.md"
    allowed.mkdir()
    outside.parent.mkdir()
    outside.write_text("secret", encoding="utf-8")
    monkeypatch.setattr(
        instruction.common,
        "find_file",
        lambda *args, **kwargs: outside,
    )

    with pytest.raises(ValueError, match="outside the allowed roots"):
        instruction.get_file_content_to_include(
            "secret.md",
            search_folders=[allowed],
            include_cwd=False,
        )
