"""Declare, read and substitute Markdown variables without a file wrapper."""

from _support import output_directory

from pymdtools.instruction import (
    get_vars_from_md_text,
    include_vars_to_md_text,
    search_include_vars_to_md_text,
    set_var_to_md_text,
)


def main() -> None:
    output = output_directory(__file__, __doc__)
    source = "# Release\n\nVersion: <!-- begin-var(version) -->pending<!-- end-var -->\n"
    declared = set_var_to_md_text(source, "version", "2.1.0")
    assert get_vars_from_md_text(declared) == {"version": "2.1.0"}
    rendered = search_include_vars_to_md_text(declared)
    (output / "declared.md").write_text(declared, encoding="utf-8")
    (output / "rendered.md").write_text(rendered, encoding="utf-8")
    # A caller can also supply variables directly, without declarations in the text.
    injected = include_vars_to_md_text(source, {"version": "2.2.0"})
    (output / "injected.md").write_text(injected, encoding="utf-8")
    assert "pending" not in rendered
    print("Declared and injected variable examples:", output)


if __name__ == "__main__":
    main()
