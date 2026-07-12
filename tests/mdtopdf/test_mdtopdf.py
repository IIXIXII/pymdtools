from __future__ import annotations

import importlib
import os
from pathlib import Path
import re
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

import pymdtools.mdtopdf as mdtopdf

PdfReader = mdtopdf.PdfReader
PdfWriter = mdtopdf.PdfWriter


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
    asset_root = tmp_path / "_pymdtools_assets" / "jasonm23-swiss"
    assert (asset_root / "style.css").is_file()
    assert (asset_root / "pilcrow.css").is_file()
    assert (asset_root / "hljs-github.min.css").is_file()
    assert "_pymdtools_assets/jasonm23-swiss/style.css" in text


def test_get_this_filename_supports_frozen_executable(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    executable = tmp_path / "app.exe"
    monkeypatch.setattr(mdtopdf.sys, "frozen", True, raising=False)
    monkeypatch.setattr(mdtopdf.sys, "executable", str(executable))

    assert mdtopdf._get_this_filename() == executable.resolve()


def test_legacy_get_this_filename_returns_text() -> None:
    assert Path(mdtopdf.__get_this_filename()) == mdtopdf._get_this_filename()


@pytest.mark.parametrize(
    "asset_name",
    [
        "",
        "../secret.css",
        "..\\secret.css",
        "/secret.css",
        "\\secret.css",
        "C:secret.css",
        "CON.css",
        "LPT9.txt",
        "style.css.",
        "bad<name.css",
    ],
)
def test_validate_asset_name_rejects_unsafe_paths(asset_name: str) -> None:
    with pytest.raises(ValueError, match="invalid layout asset path"):
        mdtopdf._validate_asset_name(asset_name)


def test_replace_layout_placeholders_keeps_unknown_placeholder(tmp_path: Path) -> None:
    html = mdtopdf._replace_layout_placeholders(
        "{{missing}} {{title}} {{author}} {{~> toc }} {{~> content}}",
        title='Doc </title><script>alert("x")</script>',
        content="<p>Body</p>",
        content_vars={"author": 'Ada"><img onerror="alert(1)'},
        layout_path=tmp_path,
        path_dest=tmp_path,
    )

    assert "{{missing}}" in html
    assert "{{~> toc" not in html
    assert "<script>" not in html
    assert "<img" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;img" in html
    assert html.endswith("<p>Body</p>")


def test_layout_assets_are_namespaced_and_include_css_dependencies(tmp_path: Path) -> None:
    source = tmp_path / "bootstrap.md"
    source.write_text("# Bootstrap\n", encoding="utf-8")

    html = mdtopdf.convert_md_to_html(source, layout="bootstrap3")

    asset_root = tmp_path / "_pymdtools_assets" / "bootstrap3"
    assert (asset_root / "css" / "bootstrap.min.css").is_file()
    assert (asset_root / "fonts" / "glyphicons-halflings-regular.woff").is_file()
    assert "_pymdtools_assets/bootstrap3/css/bootstrap.min.css" in html.read_text(
        encoding="utf-8"
    )


def test_layout_asset_copy_rejects_case_insensitive_collision(tmp_path: Path) -> None:
    layout = mdtopdf._get_layout_page("jasonm23-swiss").parent
    asset_root = tmp_path / "_pymdtools_assets" / "jasonm23-swiss"
    asset_root.mkdir(parents=True)
    (asset_root / "STYLE.css").write_text("conflict", encoding="utf-8")

    with pytest.raises(FileExistsError, match="case-insensitive"):
        mdtopdf._copy_layout_assets(layout, tmp_path)


def test_packaged_layout_references_are_self_contained() -> None:
    layouts_root = mdtopdf._get_this_filename().parent / "layouts"
    asset_pattern = re.compile(r"\{\{\s*asset\s+['\"](.*?)['\"]\s*\}\}")
    css_url_pattern = re.compile(r"url\(\s*['\"]?([^'\")]+)", re.IGNORECASE)

    for page in layouts_root.glob("*/page.html"):
        assets_root = page.parent / "assets"
        page_text = page.read_text(encoding="utf-8")
        assert not re.search(r"(?:src|href)=['\"](?:https?:)?//", page_text)
        for asset_name in asset_pattern.findall(page_text):
            assert (assets_root / mdtopdf._validate_asset_name(asset_name)).is_file()

        for css_file in assets_root.rglob("*.css"):
            css_text = css_file.read_text(encoding="utf-8", errors="replace")
            for reference in css_url_pattern.findall(css_text):
                if reference.startswith("data:"):
                    continue
                assert not reference.startswith(("http:", "https:", "//"))
                local_reference = reference.split("?", 1)[0].split("#", 1)[0]
                assert (css_file.parent / local_reference).resolve().is_file()


def test_converter_md_to_html_mistune_renders_html() -> None:
    assert "<h1>Title</h1>" in mdtopdf.converter_md_to_html_mistune("# Title")


def test_get_md_to_html_converter_falls_back_to_safe_mistune() -> None:
    converter = mdtopdf.get_md_to_html_converter("unknown")

    assert converter is mdtopdf.converter_md_to_html_mistune


def test_default_converter_escapes_raw_html_and_harmful_links(tmp_path: Path) -> None:
    source = tmp_path / "unsafe.md"
    source.write_text(
        "<script>alert(1)</script>\n\n[x](javascript:alert(2))\n",
        encoding="utf-8",
    )

    html = mdtopdf.convert_md_to_html(source)
    rendered = html.read_text(encoding="utf-8")

    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert 'href="javascript:' not in rendered


def test_get_layout_page_rejects_traversal() -> None:
    with pytest.raises(ValueError, match="invalid layout name"):
        mdtopdf._get_layout_page("../outside")


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
    monkeypatch.setattr(mdtopdf.shutil, "which", lambda name: None)

    assert mdtopdf.find_wk_html_to_pdf() == expected
    expected_name = "wkhtmltopdf.exe" if os.name == "nt" else "wkhtmltopdf"
    assert calls[0][0] == expected_name
    assert calls[0][3] == 0


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
    assert calls["kwargs"]["options"]["allow"] == str(html.parent.resolve())
    assert Path(out).is_file()


def test_convert_html_to_pdf_preserves_existing_target_on_invalid_output(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    html = tmp_path / "doc.html"
    html.write_text("<h1>Doc</h1>", encoding="utf-8")
    target = _write_pdf(tmp_path / "doc.pdf", pages=2)
    original = target.read_bytes()
    monkeypatch.setattr(mdtopdf, "find_wk_html_to_pdf", lambda: tmp_path / "wkhtmltopdf")
    monkeypatch.setattr(mdtopdf.pdfkit, "configuration", lambda **kwargs: object())

    def write_invalid_pdf(filename: Path, output: str, **kwargs: Any) -> None:
        del filename, kwargs
        Path(output).write_bytes(b"not a pdf")

    monkeypatch.setattr(mdtopdf.pdfkit, "from_file", write_invalid_pdf)

    with pytest.raises(RuntimeError, match="invalid PDF output"):
        mdtopdf.convert_html_to_pdf(html)

    assert target.read_bytes() == original


def test_metadata_from_kwargs_without_requested_metadata() -> None:
    assert mdtopdf._metadata_from_kwargs({"/Title": "Old"}, None) == {"/Title": "Old"}


def test_metadata_from_kwargs_rejects_empty_key() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        mdtopdf._metadata_from_kwargs({}, {"/": "value"})


def test_page_with_background_puts_original_content_on_top() -> None:
    calls: list[Any] = []

    class Page:
        def __copy__(self) -> "Page":
            return Page()

        def merge_page(self, page: Any) -> None:
            calls.append(page)

    original = object()
    background = type("Reader", (), {"pages": [Page()]})()

    result = mdtopdf._page_with_background(original, background)

    assert isinstance(result, Page)
    assert calls == [original]


def test_page_with_background_rejects_empty_pdf() -> None:
    background = type("Reader", (), {"pages": []})()

    with pytest.raises(ValueError, match="at least one page"):
        mdtopdf._page_with_background(object(), background)


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


def test_collect_overlay_pdfs_rejects_empty_and_conflicting_overlays(tmp_path: Path) -> None:
    empty = _write_pdf(tmp_path / "empty.pdf", pages=0)
    first = _write_pdf(tmp_path / "first.pdf", pages=1)
    second = _write_pdf(tmp_path / "second.pdf", pages=1)

    with pytest.raises(ValueError, match="at least one page"):
        mdtopdf._collect_overlay_pdfs({"background_pdf": empty})

    with pytest.raises(ValueError, match="conflicting aliases"):
        mdtopdf._collect_overlay_pdfs(
            {
                "pdf_background": first,
                "background_pdf": second,
            }
        )


def test_collect_overlay_pdfs_rejects_unknown_overlay_option(tmp_path: Path) -> None:
    overlay = _write_pdf(tmp_path / "overlay.pdf", pages=1)

    with pytest.raises(ValueError, match="unsupported PDF overlay"):
        mdtopdf._collect_overlay_pdfs({"pdf_unknown": overlay})


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


def test_pdf_features_rejects_invalid_metadata_without_modifying_target(
    tmp_path: Path,
) -> None:
    target = _write_pdf(tmp_path / "target.pdf", pages=1)
    original = target.read_bytes()

    with pytest.raises(TypeError, match="metadata must be a mapping"):
        mdtopdf.pdf_features(target, metadata=[("title", "bad")])

    assert target.read_bytes() == original


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


def test_convert_md_to_pdf_merges_explicit_metadata(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.md"
    source.write_text('<!-- var(author)="Old" -->\n# Title\n', encoding="utf-8")
    temp_dir = tmp_path / "metadata-work"
    temp_dir.mkdir()
    calls: dict[str, Any] = {}
    monkeypatch.setattr(mdtopdf.common, "make_temp_dir", lambda: temp_dir)

    def fake_convert_md_to_html(filename: Path, converter: str) -> Path:
        html = Path(filename).with_suffix(".html")
        html.write_text("<h1>Title</h1>", encoding="utf-8")
        return html

    def fake_convert_html_to_pdf(filename: Path, title: str | None = None) -> Path:
        return _write_pdf(Path(filename).with_suffix(".pdf"), pages=1)

    def fake_pdf_features(filename: Path, **kwargs: Any) -> Path:
        calls.update(kwargs)
        return filename

    monkeypatch.setattr(mdtopdf, "convert_md_to_html", fake_convert_md_to_html)
    monkeypatch.setattr(mdtopdf, "convert_html_to_pdf", fake_convert_html_to_pdf)
    monkeypatch.setattr(mdtopdf, "pdf_features", fake_pdf_features)

    mdtopdf.convert_md_to_pdf(
        source,
        metadata={"author": "New", "subject": "Audit"},
    )

    assert calls["metadata"] == {"author": "New", "subject": "Audit"}


def test_convert_md_to_pdf_preserves_existing_target_when_features_fail(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.md"
    source.write_text("# Title\n", encoding="utf-8")
    target = _write_pdf(tmp_path / "source.pdf", pages=2)
    original = target.read_bytes()
    temp_dir = tmp_path / "atomic-work"
    temp_dir.mkdir()
    monkeypatch.setattr(mdtopdf.common, "make_temp_dir", lambda: temp_dir)

    def fake_convert_md_to_html(filename: Path, converter: str) -> Path:
        del converter
        html = filename.with_suffix(".html")
        html.write_text("<h1>Title</h1>", encoding="utf-8")
        return html

    def fake_convert_html_to_pdf(filename: Path, title: str | None = None) -> Path:
        del title
        return _write_pdf(filename.with_suffix(".pdf"), pages=1)

    monkeypatch.setattr(mdtopdf, "convert_md_to_html", fake_convert_md_to_html)
    monkeypatch.setattr(mdtopdf, "convert_html_to_pdf", fake_convert_html_to_pdf)
    monkeypatch.setattr(
        mdtopdf,
        "pdf_features",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("feature failed")),
    )

    with pytest.raises(RuntimeError, match="feature failed"):
        mdtopdf.convert_md_to_pdf(source)

    assert target.read_bytes() == original
    assert not temp_dir.exists()


def test_pdf_import_falls_back_to_pypdf2(monkeypatch: Any) -> None:
    real_import_module = importlib.import_module
    fake_pypdf2 = ModuleType("PyPDF2")
    fake_pypdf2.PdfReader = PdfReader  # type: ignore[attr-defined]
    fake_pypdf2.PdfWriter = PdfWriter  # type: ignore[attr-defined]

    def import_without_pypdf(name: str, package: str | None = None) -> Any:
        if name == "pypdf":
            raise ModuleNotFoundError(name)
        if name == "PyPDF2":
            return fake_pypdf2
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", import_without_pypdf)
    reloaded = importlib.reload(mdtopdf)
    assert reloaded._pdf_module.__name__ == "PyPDF2"

    monkeypatch.undo()
    importlib.reload(mdtopdf)


def test_atomic_helpers_reject_directory_and_invalid_pdf(tmp_path: Path) -> None:
    staged = tmp_path / "staged.tmp"
    staged.write_text("content", encoding="utf-8")
    target_directory = tmp_path / "target.pdf"
    target_directory.mkdir()

    with pytest.raises(IsADirectoryError):
        mdtopdf._commit_staged_file(staged, target_directory)

    with pytest.raises(RuntimeError, match="invalid PDF output"):
        mdtopdf._validate_pdf_file(tmp_path / "missing.pdf")

    empty_pdf = _write_pdf(tmp_path / "empty.pdf", pages=0)
    with pytest.raises(ValueError, match="at least one page"):
        mdtopdf._validate_pdf_file(empty_pdf)
    mdtopdf._validate_pdf_file(empty_pdf, require_pages=False)


def test_stage_pdf_writer_cleans_failed_staging_file(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    staged = tmp_path / "failed.pdf.tmp"
    staged.write_bytes(b"")
    monkeypatch.setattr(mdtopdf, "_new_staged_path", lambda *args, **kwargs: staged)

    class BrokenWriter:
        def write(self, stream: Any) -> None:
            del stream
            raise RuntimeError("write failed")

    with pytest.raises(RuntimeError, match="write failed"):
        mdtopdf._stage_pdf_writer(BrokenWriter(), tmp_path / "target.pdf")

    assert not staged.exists()


def test_read_pdf_closes_handle_when_reader_rejects_file(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.pdf"
    invalid.write_bytes(b"invalid")

    with pytest.raises(Exception):
        mdtopdf._read_pdf(invalid)

    invalid.unlink()
    assert not invalid.exists()


def test_find_wkhtmltopdf_uses_path_and_reports_complete_failure(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    executable = tmp_path / "wkhtmltopdf"
    executable.write_text("binary", encoding="utf-8")
    monkeypatch.setattr(
        mdtopdf.shutil,
        "which",
        lambda name: str(executable) if name == "wkhtmltopdf" else None,
    )
    assert mdtopdf.find_wk_html_to_pdf() == executable.resolve()

    monkeypatch.setattr(mdtopdf.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        mdtopdf.common,
        "find_file",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()),
    )
    monkeypatch.setattr(mdtopdf, "os", SimpleNamespace(name="posix", environ={}))
    with pytest.raises(FileNotFoundError, match="was not found"):
        mdtopdf.find_wk_html_to_pdf()


def test_find_wkhtmltopdf_windows_search_handles_missing_environment(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, list[Any]]] = []
    monkeypatch.setattr(mdtopdf.shutil, "which", lambda name: None)
    monkeypatch.setattr(mdtopdf, "os", SimpleNamespace(name="nt", environ={}))

    def find_file(
        filename: str,
        start_points: list[Any],
        relative_paths: list[Any],
        *,
        max_up: int,
    ) -> Path:
        del relative_paths, max_up
        calls.append((filename, start_points))
        return tmp_path / filename

    monkeypatch.setattr(mdtopdf.common, "find_file", find_file)
    mdtopdf.find_wk_html_to_pdf()

    assert len(calls[0][1]) == 2


def test_overlay_aliases_accept_the_same_file(tmp_path: Path) -> None:
    overlay = _write_pdf(tmp_path / "overlay.pdf", pages=1)
    readers, handles = mdtopdf._collect_overlay_pdfs(
        {"pdf_background": overlay, "background_pdf": overlay}
    )
    try:
        assert list(readers) == ["background"]
        assert len(handles) == 1
    finally:
        for handle in handles:
            handle.close()


def test_pdf_features_rejects_empty_source_and_cleans_temp_dir(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    source = _write_pdf(tmp_path / "empty.pdf", pages=0)
    temp_dir = tmp_path / "empty-work"
    temp_dir.mkdir()
    monkeypatch.setattr(mdtopdf.common, "make_temp_dir", lambda: temp_dir)

    with pytest.raises(ValueError, match="source PDF"):
        mdtopdf.pdf_features(source)

    assert not temp_dir.exists()


def test_convert_md_to_pdf_rejects_non_mapping_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("# Title\n", encoding="utf-8")

    with pytest.raises(TypeError, match="metadata must be a mapping"):
        mdtopdf.convert_md_to_pdf(source, metadata=[("title", "bad")])


def test_layout_asset_namespace_rejects_invalid_layout_name() -> None:
    with pytest.raises(ValueError, match="invalid layout name"):
        mdtopdf._layout_asset_namespace(Path(".."))


def test_copy_layout_assets_rejects_assets_outside_layout(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    layout = tmp_path / "layout"
    (layout / "assets").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    real_check_folder = mdtopdf.common.check_folder

    def check_folder(path: Any) -> Path:
        if Path(path).name == "assets":
            return outside
        return real_check_folder(path)

    monkeypatch.setattr(mdtopdf.common, "check_folder", check_folder)
    with pytest.raises(ValueError, match="outside the layout"):
        mdtopdf._copy_layout_assets(layout, tmp_path)


def test_copy_layout_assets_rejects_destination_escape(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    layout = tmp_path / "layout"
    (layout / "assets").mkdir(parents=True)
    monkeypatch.setattr(
        mdtopdf,
        "_layout_asset_namespace",
        lambda layout_path: Path("..") / "escape",
    )

    with pytest.raises(ValueError, match="escapes the output"):
        mdtopdf._copy_layout_assets(layout, tmp_path)


def test_copy_layout_assets_rejects_namespace_symlink_or_file(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    layout = tmp_path / "layout"
    (layout / "assets").mkdir(parents=True)
    namespace = tmp_path / "_pymdtools_assets" / "layout"
    real_is_symlink = Path.is_symlink

    def is_symlink(path: Path) -> bool:
        return path == namespace or real_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", is_symlink)
    with pytest.raises(ValueError, match="namespace must not be a symlink"):
        mdtopdf._copy_layout_assets(layout, tmp_path)

    monkeypatch.setattr(Path, "is_symlink", real_is_symlink)
    namespace.parent.mkdir(parents=True, exist_ok=True)
    namespace.write_text("file", encoding="utf-8")
    with pytest.raises(FileExistsError, match="not a directory"):
        mdtopdf._copy_layout_assets(layout, tmp_path)


def test_copy_layout_assets_rejects_existing_symlink_entry(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    layout = tmp_path / "layout"
    (layout / "assets").mkdir(parents=True)
    namespace = tmp_path / "_pymdtools_assets" / "layout"
    namespace.mkdir(parents=True)
    existing = namespace / "existing.css"
    existing.write_text("content", encoding="utf-8")
    real_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: path == existing or real_is_symlink(path),
    )

    with pytest.raises(ValueError, match="contains a symlink"):
        mdtopdf._copy_layout_assets(layout, tmp_path)


def test_copy_layout_assets_rejects_source_symlink_or_escape(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    layout = tmp_path / "layout"
    assets = layout / "assets"
    assets.mkdir(parents=True)
    source = assets / "style.css"
    source.write_text("content", encoding="utf-8")
    real_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: path == source or real_is_symlink(path),
    )
    with pytest.raises(ValueError, match="not a regular file"):
        mdtopdf._copy_layout_assets(layout, tmp_path)

    monkeypatch.setattr(Path, "is_symlink", real_is_symlink)
    real_resolve = Path.resolve
    outside = tmp_path / "outside.css"

    def resolve(path: Path, *args: Any, **kwargs: Any) -> Path:
        if path == source:
            return outside
        return real_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ValueError, match="outside its root"):
        mdtopdf._copy_layout_assets(layout, tmp_path)


def test_copy_layout_assets_rejects_source_case_collision_and_file_escape(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    layout = tmp_path / "layout"
    assets = layout / "assets"
    assets.mkdir(parents=True)
    (assets / "a.css").write_text("a", encoding="utf-8")
    (assets / "b.css").write_text("b", encoding="utf-8")
    monkeypatch.setattr(mdtopdf, "_validate_asset_name", lambda name: Path("same.css"))
    with pytest.raises(ValueError, match="case-insensitive asset collision"):
        mdtopdf._copy_layout_assets(layout, tmp_path)

    (assets / "b.css").unlink()
    monkeypatch.setattr(
        mdtopdf,
        "_validate_asset_name",
        lambda name: Path("..") / "escape.css",
    )
    with pytest.raises(ValueError, match="destination escapes"):
        mdtopdf._copy_layout_assets(layout, tmp_path)


def test_copy_layout_assets_rejects_existing_directory_or_different_content(
    tmp_path: Path,
) -> None:
    layout = tmp_path / "layout"
    assets = layout / "assets"
    assets.mkdir(parents=True)
    (assets / "style.css").write_text("source", encoding="utf-8")
    namespace = tmp_path / "_pymdtools_assets" / "layout"
    (namespace / "style.css").mkdir(parents=True)
    with pytest.raises(FileExistsError, match="case-insensitive"):
        mdtopdf._copy_layout_assets(layout, tmp_path)

    (namespace / "style.css").rmdir()
    (namespace / "style.css").write_text("different", encoding="utf-8")
    with pytest.raises(FileExistsError, match="would overwrite"):
        mdtopdf._copy_layout_assets(layout, tmp_path)

    (namespace / "style.css").write_text("source", encoding="utf-8")
    assert mdtopdf._copy_layout_assets(layout, tmp_path).name == "layout"


def test_replace_layout_placeholders_rejects_source_escape_and_missing_namespace(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    layout = tmp_path / "layout"
    assets = layout / "assets"
    assets.mkdir(parents=True)
    source = assets / "style.css"
    source.write_text("content", encoding="utf-8")
    outside = tmp_path / "outside.css"
    outside.write_text("outside", encoding="utf-8")
    monkeypatch.setattr(mdtopdf, "_copy_layout_assets", lambda *args: Path("assets"))
    monkeypatch.setattr(mdtopdf.common, "check_file", lambda path: outside)

    with pytest.raises(ValueError, match="outside its root"):
        mdtopdf._replace_layout_placeholders(
            "{{asset 'style.css'}}",
            title="",
            content="",
            content_vars={},
            layout_path=layout,
            path_dest=tmp_path,
        )

    real_asset_re = mdtopdf.ASSET_RE

    class InconsistentAssetPattern:
        @staticmethod
        def search(text: str) -> None:
            del text
            return None

        @staticmethod
        def fullmatch(text: str) -> Any:
            return real_asset_re.fullmatch(text)

    monkeypatch.setattr(mdtopdf, "ASSET_RE", InconsistentAssetPattern())
    monkeypatch.setattr(mdtopdf.common, "check_file", lambda path: source)
    with pytest.raises(RuntimeError, match="namespace was not initialized"):
        mdtopdf._replace_layout_placeholders(
            "{{asset 'style.css'}}",
            title="",
            content="",
            content_vars={},
            layout_path=layout,
            path_dest=tmp_path,
        )
