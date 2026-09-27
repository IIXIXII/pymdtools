"""Render a Markdown document to PDF with page options and explicit metadata."""

import shutil

from _support import DATA, output_directory

from pymdtools.mdtopdf import convert_md_to_pdf
from pymdtools.options import PdfFeatures
from pymdtools.pdf_backend import PdfOptions


def main() -> None:
    output = output_directory(__file__, __doc__)
    from pypdf import PdfReader  # Requires pymdtools[pdf].

    source = output / "guide.md"
    shutil.copyfile(DATA / "document.md", source)
    pdf = convert_md_to_pdf(
        source,
        options=PdfOptions(timeout=60, page_format="Letter"),
        features=PdfFeatures(metadata={"Title": "Example handbook", "Author": "Example team"}),
    )
    reader = PdfReader(pdf)
    assert reader.metadata.title == "Example handbook"
    assert "Sample guide" in reader.pages[0].extract_text()
    print("PDF:", pdf)
    print("Pages:", len(reader.pages), "Title:", reader.metadata.title)


if __name__ == "__main__":
    main()
