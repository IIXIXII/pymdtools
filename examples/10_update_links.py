"""Rename selected links and apply sequential replacements to one document."""

from _support import DATA, output_directory

from pymdtools.mdcommon import search_link_in_md_text, update_links_in_md_text


def main() -> None:
    output = output_directory(__file__, __doc__)
    source = (DATA / "links.md").read_text(encoding="utf-8")
    result = update_links_in_md_text(
        source,
        [
            {"name_to_replace": "Guide", "name": "Handbook", "url": "handbook.md"},
            {"name_to_replace": "Handbook", "name": "Start here", "url": "start.md"},
            {"name_to_replace": "API", "name": "API v2", "url": "api/v2.md"},
        ],
    )
    urls = {link["name"]: link["url"] for link in search_link_in_md_text(result)}
    assert urls["Start here"] == "start.md"
    assert urls["API v2"] == "api/v2.md"
    assert urls["API again"] == "api.md"  # The unselected reference user stays unchanged.
    (output / "updated.md").write_text(result, encoding="utf-8")
    print("Changed links:", urls)


if __name__ == "__main__":
    main()
