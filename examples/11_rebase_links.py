"""Move relative link targets while preserving spaces, accents, queries and anchors."""

from _support import output_directory

from pymdtools.mdcommon import move_base_path_in_md_text, search_link_in_md_text


def main() -> None:
    output = output_directory(__file__, __doc__)
    source = (
        "[Guide](guide.md?mode=print#install)\n\n"
        "[Website](https://example.com) and [Here](#section).\n\n"
        "[Release](release(v2).md)\n"
    )
    result = move_base_path_in_md_text(source, "Guides été")
    urls = {link["name"]: link["url"] for link in search_link_in_md_text(result)}
    assert urls["Guide"] == "Guides%20%C3%A9t%C3%A9/guide.md?mode=print#install"
    assert urls["Here"] == "#section"
    assert urls["Website"] == "https://example.com"
    (output / "rebased.md").write_text(result, encoding="utf-8")
    print(result)


if __name__ == "__main__":
    main()
