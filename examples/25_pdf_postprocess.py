"""Balance PDF pages, apply a background and watermark, and set final metadata."""

from _support import output_directory

from pymdtools.mdtopdf import check_odd_pages, convert_html_to_pdf, pdf_features
from pymdtools.options import PdfFeatures
from pymdtools.pdf_backend import PdfOptions


def main() -> None:
    output = output_directory(__file__, __doc__)
    from pypdf import PdfReader

    sources = {
        "document": "<h1>Quarterly report</h1><p>One page of original content.</p>",
        "background": '<p style="position:absolute;bottom:0;color:#666">Example stationery</p>',
        "watermark": '<p style="margin-top:250px;color:#ddd;font-size:64pt">DRAFT</p>',
    }
    for name, content in sources.items():
        html = output / f"{name}.html"
        html.write_text(
            '<!doctype html><meta charset="utf-8"><style>body{font-family:sans-serif}</style>'
            + content,
            encoding="utf-8",
        )
        convert_html_to_pdf(html, options=PdfOptions(timeout=60))

    target = output / "document.pdf"
    assert len(PdfReader(target).pages) == 1
    check_odd_pages(target)  # Despite its name, this ensures an EVEN page count.
    # Set final metadata after page balancing, which rebuilds the PDF.
    pdf_features(
        target,
        features=PdfFeatures(
            metadata={"Title": "Quarterly report - draft", "Author": "Example team"},
            background_pdf="background.pdf",
            watermark_pdf="watermark.pdf",
            path=output,
        ),
    )
    reader = PdfReader(target)
    assert len(reader.pages) == 2
    assert reader.metadata.title == "Quarterly report - draft"
    assert "DRAFT" in reader.pages[0].extract_text()
    assert "Example stationery" in reader.pages[0].extract_text()
    print("Final PDF:", target)
    print("Page balancing also creates a .bak copy; overlays apply to both pages.")


if __name__ == "__main__":
    main()
