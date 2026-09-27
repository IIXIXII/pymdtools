"""Read legacy text, write UTF-8 and distinguish URL encoding from filename slugs."""

import json

from _support import output_directory

from pymdtools.common import (
    encode_path_url,
    get_file_content,
    get_valid_filename,
    set_file_content,
    slugify,
)


def main() -> None:
    output = output_directory(__file__, __doc__)
    original = output / "legacy.txt"
    original.write_bytes("Café, été et Noël.\n".encode("cp1252"))
    # Prefer an explicit encoding when it is known; detection is also available.
    text = get_file_content(original, encoding="cp1252")
    set_file_content(output / "utf8.txt", text, encoding="utf-8")
    path = "Guides été/My Report.md"
    results = {
        "url_preserving_the_existing_path": encode_path_url(path),
        "slug_for_a_new_name": slugify("My summer report"),
        "valid_filename": get_valid_filename("Quarterly report.txt"),
    }
    assert results["url_preserving_the_existing_path"].startswith("Guides%20%C3%A9t%C3%A9/")
    (output / "paths.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(text, results)


if __name__ == "__main__":
    main()
