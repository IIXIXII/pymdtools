"""Render local HTML, an SVG, a table and a CSS page break into a two-page PDF."""

import shutil

from _support import DATA, output_directory

from pymdtools.mdtopdf import convert_html_to_pdf
from pymdtools.pdf_backend import PdfOptions


def main() -> None:
    output = output_directory(__file__, __doc__)
    from pypdf import PdfReader

    for name in ("print.html", "diagram.svg"):
        shutil.copyfile(DATA / name, output / name)
    pdf = convert_html_to_pdf(
        output / "print.html",
        title="Local resources",
        options=PdfOptions(timeout=60, page_format="A4", allow_network=False),
    )
    reader = PdfReader(pdf)
    assert len(reader.pages) == 2
    assert "Second page" in reader.pages[1].extract_text()
    assert "café" in reader.pages[0].extract_text()
    print("Two-page PDF with a local SVG:", pdf)


if __name__ == "__main__":
    main()
