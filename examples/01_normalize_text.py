"""Normalize Markdown in memory and check that a second pass is unchanged."""

from _support import output_directory

from pymdtools.normalize import md_beautifier


def main() -> None:
    output = output_directory(__file__, __doc__)
    source = "Title\n=====\n\n* first item\n* second item\n\nA **bold** word.\n"
    normalized = md_beautifier(source)
    assert md_beautifier(normalized) == normalized
    (output / "before.md").write_text(source, encoding="utf-8")
    (output / "after.md").write_text(normalized, encoding="utf-8")
    print(normalized)
    print("Compare before.md and after.md in", output)


if __name__ == "__main__":
    main()
