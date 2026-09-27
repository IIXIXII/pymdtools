"""Edit a MarkdownContent buffer, its title and variables, then save it."""

from _support import output_directory

from pymdtools.mdfile import MarkdownContent


def main() -> None:
    output = output_directory(__file__, __doc__)
    document = MarkdownContent(
        output / "document.md",
        content="# Draft\n\nAuthor: <!-- begin-var(author) -->unknown<!-- end-var -->\n",
        backup=False,
    )
    document.title = "Project handbook"
    document["author"] = "Example team"
    document["status"] = "Draft"
    print("Variables:", dict(document.items()))
    del document["status"]
    document.process_tags()
    assert document.save_needed
    document.write()
    assert not document.save_needed
    assert MarkdownContent(output / "document.md").title == "Project handbook"
    print("Saved:", document.full_filename)


if __name__ == "__main__":
    main()
