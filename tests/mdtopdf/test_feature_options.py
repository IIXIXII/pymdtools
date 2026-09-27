import pytest
from pypdf import PdfReader, PdfWriter

from pymdtools import mdtopdf
from pymdtools.options import PdfFeatures


def write_pdf(path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with path.open("wb") as stream:
        writer.write(stream)


def test_typed_features_apply_metadata_and_overlays(tmp_path):
    target, overlay = tmp_path / "document.pdf", tmp_path / "overlay.pdf"
    write_pdf(target)
    write_pdf(overlay)
    mdtopdf.pdf_features(
        target,
        features=PdfFeatures(
            metadata={"Title": "Typed title"},
            watermark_pdf="overlay.pdf",
            path=tmp_path,
        ),
    )
    with target.open("rb") as stream:
        reader = PdfReader(stream)
        assert len(reader.pages) == 1
        assert reader.metadata.title == "Typed title"


def test_explicit_metadata_overrides_typed_metadata(tmp_path):
    target = tmp_path / "document.pdf"
    write_pdf(target)
    mdtopdf.pdf_features(
        target, features=PdfFeatures(metadata={"Title": "Typed"}), metadata={"Title": "Explicit"}
    )
    with target.open("rb") as stream:
        assert PdfReader(stream).metadata.title == "Explicit"


def test_misspelled_features_fail_without_touching_the_pdf(tmp_path):
    target = tmp_path / "document.pdf"
    write_pdf(target)
    before = target.read_bytes()
    with pytest.raises(ValueError, match="metadta"):
        mdtopdf.pdf_features(target, metadta={"Title": "Typo"})
    assert target.read_bytes() == before


def test_markdown_pipeline_passes_typed_features_to_postprocessing(tmp_path, monkeypatch):
    source = tmp_path / "document.md"
    source.write_text("# Title", encoding="utf-8")
    monkeypatch.setattr(mdtopdf, "render_pdf", lambda source, target, options: write_pdf(target))
    target = mdtopdf.convert_md_to_pdf(source, features=PdfFeatures(metadata={"Title": "Typed"}))
    with target.open("rb") as stream:
        assert PdfReader(stream).metadata.title == "Typed"
