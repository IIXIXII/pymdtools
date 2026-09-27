"""Publish Markdown as a complete HTML page with local assets and license notices."""

import shutil

from _support import DATA, output_directory

from pymdtools.mdtopdf import convert_md_to_html


def main() -> None:
    output = output_directory(__file__, __doc__)
    source = output / "guide.md"
    shutil.copyfile(DATA / "document.md", source)
    # The default Mistune converter escapes raw HTML in the Markdown source.
    html = convert_md_to_html(source, layout="github", path_dest=output)
    assert html.is_file()
    notices = output / "_pymdtools_assets" / "github" / "LICENSES.txt"
    assert notices.is_file()
    print("Open in a browser:", html)
    print("Keep the entire _pymdtools_assets directory when sharing the page.")


if __name__ == "__main__":
    main()
