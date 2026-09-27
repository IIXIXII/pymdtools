"""Build a report from JSON, reusable content and variables, then publish HTML."""

import json

from _support import DATA, output_directory

from pymdtools.mdfile import MarkdownContent
from pymdtools.mdtopdf import convert_md_to_html
from pymdtools.options import IncludeOptions


def main() -> None:
    output = output_directory(__file__, __doc__)
    data = json.loads((DATA / "report.json").read_text(encoding="utf-8"))
    sections = "\n".join(
        f"- **{item['name']}**: {item['pages']} pages ({item['status']})."
        for item in data["sections"]
    )
    document = MarkdownContent(
        output / "report.md",
        content=(
            "# Draft\n\nPeriod: <!-- begin-var(period) -->pending<!-- end-var -->\n\n"
            "<!-- include-file(introduction.md) -->\n\n"
            f"## Progress\n\n{sections}\n\n"
            "<!-- begin-include(support) -->pending<!-- end-include -->\n"
        ),
        include_options=IncludeOptions(
            search_folders=(DATA, DATA / "snippets"), refs_depth=1, render_mode="raw"
        ),
        backup=False,
    )
    document.title = data["title"]
    document["period"] = data["period"]
    document["author"] = data["author"]
    document.process_tags()
    assert "pending" not in (document.content or "")
    document.beautify()
    document.write()
    html = convert_md_to_html(output / "report.md", layout="github")
    print("Markdown:", document.full_filename)
    print("HTML:", html)


if __name__ == "__main__":
    main()
