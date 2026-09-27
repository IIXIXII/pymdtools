"""Refresh reusable named sections while retaining their include markers."""

from _support import DATA, output_directory

from pymdtools.instruction import get_refs_from_md_file, include_refs_to_md_text


def main() -> None:
    output = output_directory(__file__, __doc__)
    references = get_refs_from_md_file(DATA / "references" / "shared.md")
    source = "# Handbook\n\n<!-- begin-include(support) -->Old text<!-- end-include -->\n"
    result = include_refs_to_md_text(source, references)
    assert "Old text" not in result
    assert include_refs_to_md_text(result, references) == result
    (output / "handbook.md").write_text(result, encoding="utf-8")
    print("Available sections:", ", ".join(references))
    print("Refreshed:", output / "handbook.md")


if __name__ == "__main__":
    main()
