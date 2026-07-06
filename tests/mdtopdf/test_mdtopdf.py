from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from PyPDF2 import PdfReader, PdfWriter

import pymdtools.mdtopdf as mdtopdf


def _write_pdf(path: Path, *, pages: int = 1, metadata: dict[str, str] | None = None) -> Path:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    if metadata:
        writer.add_metadata(metadata)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def _page_count(path: Path) -> int:
    with path.open("rb") as stream:
        return len(PdfReader(stream).pages)


def test_check_odd_pages_adds_blank_page_to_odd_pdf(tmp_path: Path) -> None:
    pdf = _write_pdf(tmp_path / "odd.pdf", pages=1)

    returned = mdtopdf.check_odd_pages(pdf)

    assert Path(returned) == pdf.resolve()
    assert _page_count(pdf) == 2


def test_check_odd_pages_leaves_even_pdf_unchanged(tmp_path: Path) -> None:
    pdf = _write_pdf(tmp_path / "even.pdf", pages=2)

    returned = mdtopdf.check_odd_pages(pdf)

    assert Path(returned) == pdf.resolve()
    assert _page_count(pdf) == 2


def test_convert_md_to_html_uses_packaged_layout_and_copies_assets(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        '<!-- var(author)="Ada" -->\n'
        '<!-- var(description)="Desc" -->\n'
        '<!-- var(keywords)="one,two" -->\n'
        "# Title\n\nBody\n",
        encoding="utf-8",
    )

    html = Path(mdtopdf.convert_md_to_html(source, path_dest=tmp_path, converter="markdown"))

    assert html == tmp_path.resolve() / "source.html"
    text = html.read_text(encoding="utf-8")
    assert "<title>Title</title>" in text
    assert "<h1>Title</h1>" in text
    assert 'content="Ada"' in text
    assert (tmp_path / "style.css").is_file()
    assert (tmp_path / "pilcrow.css").is_file()
    assert (tmp_path / "hljs-github.min.css").is_file()


def test_get_this_filename_supports_frozen_executable(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    executable = tmp_path / "app.exe"
    monkeypatch.setattr(mdtopdf.sys, "frozen", True, raising=False)
    monkeypatch.setattr(mdtopdf.sys, "executable", str(executable))

    assert mdtopdf._get_this_filename() == executable.resolve()


@pytest.mark.parametrize("asset_name", ["", "../secret.css", "..\\secret.css"])
def test_validate_asset_name_rejects_unsafe_paths(asset_name: str) -> None:
    with pytest.raises(ValueError, match="invalid layout asset path"):
        mdtopdf._validate_asset_name(asset_name)


def test_replace_layout_placeholders_keeps_unknown_placeholder(tmp_path: Path) -> None:
    html = mdtopdf._replace_layout_placeholders(
        "{{missing}} {{title}} {{~> content}}",
        title="Doc",
        content="<p>Body</p>",
        content_vars={},
        layout_path=tmp_path,
        path_dest=tmp_path,
    )

    assert html == "{{missing}} Doc <p>Body</p>"


def test_converter_md_to_html_mistune_renders_html() -> None:
    assert "<h1>Title</h1>" in mdtopdf.converter_md_to_html_mistune("# Title")


def test_get_md_to_html_converter_falls_back_to_markdown() -> None:
    converter = mdtopdf.get_md_to_html_converter("unknown")

    assert converter is mdtopdf.converter_md_to_html_markdown


def test_convert_md_to_html_defaults_to_source_folder_and_empty_title(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("Body\n", encoding="utf-8")

    html = mdtopdf.convert_md_to_html(source)

    assert html == tmp_path.resolve() / "source.html"
    text = html.read_text(encoding="utf-8")
    assert "<title></title>" in text
    assert "<p>Body</p>" in text


def test_convert_md_to_html_rejects_empty_file(tmp_path: Path) -> None:
    source = tmp_path / "empty.md"
    source.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="seems empty"):
        mdtopdf.convert_md_to_html(source)


def test_find_wk_html_to_pdf_uses_common_find_file(monkeypatch: Any, tmp_path: Path) -> None:
    expected = tmp_path / "wkhtmltopdf.exe"
    calls: list[tuple[str, list[Any], list[Any], int]] = []

    def fake_find_file(
        filename: str,
        start_points: list[Any],
        relative_paths: list[Any],
        *,
        max_up: int,
    ) -> Path:
        calls.append((filename, start_points, relative_paths, max_up))
        return expected

    monkeypatch.setattr(mdtopdf.common, "find_file", fake_find_file)

    assert mdtopdf.find_wk_html_to_pdf() == expected
    assert calls[0][0] == "wkhtmltopdf.exe"
    assert calls[0][3] == 4


def test_convert_html_to_pdf_uses_stem_as_default_title(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    html = tmp_path / "doc.html"
    html.write_text("<h1>Doc</h1>", encoding="utf-8")
    calls: dict[str, Any] = {}

    monkeypatch.setattr(mdtopdf, "find_wk_html_to_pdf", lambda: tmp_path / "wkhtmltopdf.exe")
    monkeypatch.setattr(mdtopdf.pdfkit, "configuration", lambda wkhtmltopdf: object())

    def fake_from_file(filename: Path, pdf_filename: str, **kwargs: Any) -> None:
        calls["options"] = kwargs["options"]
        _write_pdf(Path(pdf_filename), pages=1)

    monkeypatch.setattr(mdtopdf.pdfkit, "from_file", fake_from_file)

    mdtopdf.convert_html_to_pdf(html)

    assert calls["options"]["header-center"] == "doc"


def test_convert_html_to_pdf_uses_pdfkit_without_real_wkhtmltopdf(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    html = tmp_path / "doc.html"
    html.write_text("<h1>Doc</h1>", encoding="utf-8")
    expected_config = object()
    calls: dict[str, Any] = {}

    monkeypatch.setattr(mdtopdf, "find_wk_html_to_pdf", lambda: tmp_path / "wkhtmltopdf.exe")

    def fake_configuration(wkhtmltopdf: Path) -> object:
        calls["wkhtmltopdf"] = wkhtmltopdf
        return expected_config

    monkeypatch.setattr(mdtopdf.pdfkit, "configuration", fake_configuration)

    def fake_from_file(filename: Path, pdf_filename: str, **kwargs: Any) -> None:
        calls["filename"] = filename
        calls["pdf_filename"] = pdf_filename
        calls["kwargs"] = kwargs
        _write_pdf(Path(pdf_filename), pages=1)

    monkeypatch.setattr(mdtopdf.pdfkit, "from_file", fake_from_file)

    out = mdtopdf.convert_html_to_pdf(html, title="Custom")

    assert Path(out) == tmp_path / "doc.pdf"
    assert calls["filename"] == html.resolve()
    assert calls["wkhtmltopdf"] == tmp_path / "wkhtmltopdf.exe"
    assert calls["kwargs"]["configuration"] is expected_config
    assert calls["kwargs"]["options"]["header-center"] == "Custom"
    assert Path(out).is_file()


def test_metadata_from_kwargs_without_requested_metadata() -> None:
    assert mdtopdf._metadata_from_kwargs({"/Title": "Old"}, None) == {"/Title": ""}


def test_collect_overlay_pdfs_supports_legacy_pdf_prefix(tmp_path: Path) -> None:
    background = _write_pdf(tmp_path / "background.pdf", pages=1)

    pdf_args, handles = mdtopdf._collect_overlay_pdfs(
        {
            "pdf_background": background,
            "ignored": "value",
        },
    )

    try:
        assert set(pdf_args) == {"background"}
        assert len(handles) == 1
        assert len(pdf_args["background"].pages) == 1
    finally:
        for handle in handles:
            handle.close()


def test_pdf_features_updates_metadata_merges_pdfs_and_removes_temp_dir(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    target = _write_pdf(tmp_path / "target.pdf", pages=2, metadata={"/Title": "Old"})
    _write_pdf(tmp_path / "background.pdf", pages=1)
    _write_pdf(tmp_path / "background_first_page.pdf", pages=1)
    _write_pdf(tmp_path / "watermark.pdf", pages=1)
    temp_dir = tmp_path / "work"
    temp_dir.mkdir()
    monkeypatch.setattr(mdtopdf.common, "make_temp_dir", lambda: temp_dir)

    returned = mdtopdf.pdf_features(
        target,
        path=tmp_path,
        metadata={"title": "New", "author": "Ada"},
        background_pdf="background.pdf",
        background_first_page_pdf="background_first_page.pdf",
        watermark_pdf="watermark.pdf",
    )

    assert Path(returned) == target.resolve()
    assert not temp_dir.exists()
    with target.open("rb") as stream:
        reader = PdfReader(stream)
        assert len(reader.pages) == 2
        assert reader.metadata["/Title"] == "New"
        assert reader.metadata["/Author"] == "Ada"


def test_pdf_features_applies_background_to_all_pages(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    target = _write_pdf(tmp_path / "target.pdf", pages=2)
    background = _write_pdf(tmp_path / "background.pdf", pages=1)
    temp_dir = tmp_path / "background-work"
    temp_dir.mkdir()
    monkeypatch.setattr(mdtopdf.common, "make_temp_dir", lambda: temp_dir)

    returned = mdtopdf.pdf_features(target, pdf_background=background)

    assert returned == target.resolve()
    assert not temp_dir.exists()
    assert _page_count(target) == 2


def test_pdf_features_without_overlays_keeps_page_count(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    target = _write_pdf(tmp_path / "target.pdf", pages=2)
    temp_dir = tmp_path / "plain-work"
    temp_dir.mkdir()
    monkeypatch.setattr(mdtopdf.common, "make_temp_dir", lambda: temp_dir)

    returned = mdtopdf.pdf_features(target)

    assert returned == target.resolve()
    assert not temp_dir.exists()
    assert _page_count(target) == 2


def test_convert_md_to_pdf_cleans_temp_dir_and_applies_pdf_features(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.md"
    source.write_text('<!-- var(page:title)="Page Title" -->\n# Title\n', encoding="utf-8")
    temp_dir = tmp_path / "convert-work"
    temp_dir.mkdir()
    calls: dict[str, Any] = {}

    monkeypatch.setattr(mdtopdf.common, "make_temp_dir", lambda: temp_dir)

    def fake_convert_md_to_html(filename: Path, converter: str) -> Path:
        calls["md_to_html"] = (filename, converter)
        html = Path(filename).with_suffix(".html")
        html.write_text("<h1>Title</h1>", encoding="utf-8")
        return html

    def fake_convert_html_to_pdf(filename: Path, title: str | None = None) -> Path:
        calls["html_to_pdf"] = (filename, title)
        return _write_pdf(Path(filename).with_suffix(".pdf"), pages=1)

    def fake_pdf_features(filename: Path, filename_ext: str = ".pdf", **kwargs: Any) -> Path:
        calls["pdf_features"] = (filename, filename_ext, kwargs)
        return filename

    monkeypatch.setattr(mdtopdf, "convert_md_to_html", fake_convert_md_to_html)
    monkeypatch.setattr(mdtopdf, "convert_html_to_pdf", fake_convert_html_to_pdf)
    monkeypatch.setattr(mdtopdf, "pdf_features", fake_pdf_features)

    out = mdtopdf.convert_md_to_pdf(source, option="value")

    assert Path(out) == tmp_path / "source.pdf"
    assert Path(out).is_file()
    assert not temp_dir.exists()
    assert calls["md_to_html"][1] == "mistune"
    assert calls["html_to_pdf"][1] == "Page Title"
    assert calls["pdf_features"][1] == ".pdf"
    assert calls["pdf_features"][2]["option"] == "value"
    assert calls["pdf_features"][2]["metadata"]["page:title"] == "Page Title"


def test_convert_md_to_pdf_uses_title_metadata_when_page_title_is_absent(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.md"
    source.write_text('<!-- var(title)="Doc Title" -->\n# Title\n', encoding="utf-8")
    temp_dir = tmp_path / "title-work"
    temp_dir.mkdir()
    calls: dict[str, Any] = {}

    monkeypatch.setattr(mdtopdf.common, "make_temp_dir", lambda: temp_dir)

    def fake_convert_md_to_html(filename: Path, converter: str) -> Path:
        html = Path(filename).with_suffix(".html")
        html.write_text("<h1>Title</h1>", encoding="utf-8")
        return html

    def fake_convert_html_to_pdf(filename: Path, title: str | None = None) -> Path:
        calls["title"] = title
        return _write_pdf(Path(filename).with_suffix(".pdf"), pages=1)

    monkeypatch.setattr(mdtopdf, "convert_md_to_html", fake_convert_md_to_html)
    monkeypatch.setattr(mdtopdf, "convert_html_to_pdf", fake_convert_html_to_pdf)
    monkeypatch.setattr(mdtopdf, "pdf_features", lambda filename, **kwargs: filename)

    mdtopdf.convert_md_to_pdf(source)

    assert calls["title"] == "Doc Title"
