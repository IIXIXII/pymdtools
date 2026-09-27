"""Inventory inline/reference links, classify external URLs and export JSON."""

import json

from _support import DATA, output_directory

from pymdtools.mdcommon import is_external_link, search_link_in_md_file


def main() -> None:
    output = output_directory(__file__, __doc__)
    links = search_link_in_md_file(DATA / "links.md")
    for link in links:
        print(f"Line {link['line']}: {link['name']} -> {link['url']}")
    assert len(links) == 6  # Repeated reference users are separate occurrences.
    inventory = [dict(link, external=is_external_link(str(link["url"]))) for link in links]
    (output / "links.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print("Images and links inside code are excluded. Saved:", output / "links.json")


if __name__ == "__main__":
    main()
