"""Render the same document with GitHub, Bootstrap and Solarized layouts."""

import shutil

from _support import DATA, output_directory

from pymdtools.mdtopdf import convert_md_to_html


def main() -> None:
    output = output_directory(__file__, __doc__)
    source = output / "guide.md"
    shutil.copyfile(DATA / "document.md", source)
    links = []
    # See LICENSES-3rd-party.md for each layout's assets and terms.
    for layout in ("github", "bootstrap3", "thomasf-solarizedcssdark"):
        destination = output / layout
        destination.mkdir(exist_ok=True)
        html = convert_md_to_html(source, layout=layout, path_dest=destination)
        links.append(f'<li><a href="{layout}/{html.name}">{layout}</a></li>')
        assert (destination / "_pymdtools_assets" / layout / "LICENSES.txt").is_file()
    index = output / "index.html"
    index.write_text(
        '<!doctype html><meta charset="utf-8"><h1>Layout gallery</h1><ul>'
        + "\n".join(links)
        + "</ul>",
        encoding="utf-8",
    )
    print("Open the gallery:", index)


if __name__ == "__main__":
    main()
