import io
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from pymdtools._rendering import pdf_backend as backend


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_timeout_must_be_finite_positive(timeout):
    with pytest.raises(ValueError, match="timeout"):
        backend.PdfOptions(timeout=timeout)


def test_unknown_page_format_rejected():
    with pytest.raises(ValueError, match="page_format"):
        backend.PdfOptions(page_format="unknown")


def test_resource_policy(tmp_path):
    allowed = tmp_path / "assets"
    allowed.mkdir()
    (allowed / "My image.svg").write_text("<svg/>")
    (tmp_path / "secret").write_text("secret")
    roots = (allowed,)
    assert (
        backend.local_resource("https://pymdtools.invalid/My%20image.svg", roots)
        == allowed / "My image.svg"
    )
    for url in [
        "https://example.com/image.svg",
        "file:///secret",
        "https://pymdtools.invalid/../secret",
        "https://pymdtools.invalid/%2e%2e/secret",
        "https://pymdtools.invalid/C:/secret",
        "https://pymdtools.invalid/a%5Cb",
        "https://pymdtools.invalid/missing",
    ]:
        assert backend.local_resource(url, roots) is None


def test_worker_errors_and_timeout_are_actionable(monkeypatch, tmp_path):
    source = tmp_path / "doc.html"
    target = tmp_path / "doc.pdf"
    for message in ["Install Chromium", ""]:
        monkeypatch.setattr(
            backend.subprocess,
            "run",
            lambda *a, message=message, **kw: SimpleNamespace(returncode=1, stderr=message),
        )
        with pytest.raises(backend.PdfRenderError):
            backend.render_pdf(source, target, backend.PdfOptions())

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("worker", kwargs["timeout"])

    monkeypatch.setattr(backend.subprocess, "run", timeout)
    with pytest.raises(backend.PdfRenderError, match="exceeded"):
        backend.render_pdf(source, target, backend.PdfOptions(timeout=1))


def test_worker_receives_options(monkeypatch, tmp_path):
    requests = []

    def run(*args, **kwargs):
        requests.append(json.loads(kwargs["input"]))
        assert kwargs["timeout"] == 5
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(backend.subprocess, "run", run)
    backend.render_pdf(tmp_path / "x.html", tmp_path / "x.pdf", backend.PdfOptions(timeout=5))
    assert requests[0]["options"]["allow_network"] is False


def test_missing_browser_extra(monkeypatch, tmp_path):
    import builtins

    real_import = builtins.__import__

    def without_playwright(name, *args, **kwargs):
        if name == "playwright.sync_api":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_playwright)
    with pytest.raises(backend.PdfRenderError, match="install chromium"):
        backend.render_in_process(tmp_path / "x", tmp_path / "out", backend.PdfOptions())


@pytest.mark.parametrize("allow_network", [False, True])
def test_browser_resource_routing_and_cleanup(monkeypatch, tmp_path, allow_network):
    import playwright.sync_api

    source = tmp_path / "x.html"
    source.write_text("<h1>Doc</h1>")
    (tmp_path / "blob.unknownext").write_bytes(b"test")
    actions = []

    class Route:
        def __init__(self, url):
            self.request = SimpleNamespace(url=url)

        def fulfill(self, **kwargs):
            actions.append(("serve", kwargs))

        def abort(self):
            actions.append(("abort", self.request.url))

        def continue_(self):
            actions.append(("network", self.request.url))

    class Browser:
        def new_context(self, **kwargs):
            assert kwargs["java_script_enabled"] is False
            return self

        def route(self, pattern, handler):
            for path in [
                "https://pymdtools.invalid/x.html",
                "https://pymdtools.invalid/blob.unknownext",
                "https://pymdtools.invalid/missing",
                "https://example.com/image",
                "file:///secret",
            ]:
                handler(Route(path))

        def new_page(self):
            return self

        def goto(self, url, **kwargs):
            assert url.endswith("/x.html")

        def pdf(self, **kwargs):
            assert "&lt;title&gt;" in kwargs["header_template"]

        def close(self):
            actions.append(("close", None))

    class Playwright:
        def __enter__(self):
            return SimpleNamespace(chromium=SimpleNamespace(launch=lambda **kw: Browser()))

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(playwright.sync_api, "sync_playwright", Playwright)
    backend.render_in_process(
        source,
        tmp_path / "out.pdf",
        backend.PdfOptions(
            title="<title>",
            allow_network=allow_network,
            asset_root=str(tmp_path) if allow_network else None,
        ),
    )
    assert sum(action == "serve" for action, _ in actions) == 2
    assert sum(action == "network" for action, _ in actions) == int(allow_network)
    assert actions[-1][0] == "close"


def test_worker_entrypoint(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        backend.sys,
        "stdin",
        io.StringIO(json.dumps({"source": "x", "destination": "y", "options": {}})),
    )
    monkeypatch.setattr(backend, "render_in_process", lambda *args: calls.append(args))
    backend.main()
    assert calls[0][:2] == (Path("x"), Path("y"))


@pytest.mark.pdf_integration
@pytest.mark.skipif(
    os.environ.get("PYMDTOOLS_PDF_TESTS") != "1", reason="Opt in to installed Chromium"
)
def test_real_chromium_document_and_atomic_pipeline(tmp_path):
    from pypdf import PdfReader

    from pymdtools.mdtopdf import convert_html_to_pdf, convert_md_to_pdf

    source = tmp_path / "document.html"
    source.write_text(
        """<!doctype html><meta charset="utf-8">
    <style>body {font: 12pt sans-serif} table {border-collapse:collapse} td {border:1px solid #888;padding:8px} .next {break-before:page}</style>
    <h1>Document de référence</h1><p>Accents : été, Noël. <a href="https://example.com">Lien</a></p>
    <table><tr><td>Produit</td><td>Montant</td></tr><tr><td>Exemple</td><td>42 EUR</td></tr></table>
    <img src="figure.svg"><p class="next">Deuxième page</p>""",
        encoding="utf-8",
    )
    (tmp_path / "figure.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="60"><rect width="200" height="60" fill="#246"/></svg>'
    )
    pdf = convert_html_to_pdf(source)
    reader = PdfReader(pdf)
    assert len(reader.pages) == 2
    assert "référence" in reader.pages[0].extract_text()
    assert "Deuxième" in reader.pages[1].extract_text()
    assert reader.pages[0].get("/Annots")
    md = tmp_path / "markdown.md"
    md.write_text("# Document\n\nTexte avec **gras**.\n", encoding="utf-8")
    assert "Document" in PdfReader(convert_md_to_pdf(md)).pages[0].extract_text()
