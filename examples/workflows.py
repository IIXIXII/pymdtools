"""Run assembly, link editing and offline translation; optionally render PDF."""

from __future__ import annotations

import argparse
from pathlib import Path

from pymdtools.mdcommon import move_base_path_in_md_text, search_link_in_md_text
from pymdtools.mdfile import MarkdownContent
from pymdtools.mdtopdf import convert_md_to_html, convert_md_to_pdf
from pymdtools.options import IncludeOptions, PdfFeatures
from pymdtools.pdf_backend import PdfOptions
from pymdtools.translate import TranslationClient, translate_md


def offline_translation(text: str, src: str, dest: str, **kwargs: object) -> str:
    """Demonstration transport: no document leaves this machine."""
    return text.replace("Bonjour", "Hello")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pdf", action="store_true", help="Requires the PDF extra and Chromium")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "snippet.md").write_text("Bonjour **tout le monde**.\n", encoding="utf-8")
    document = MarkdownContent(
        output / "document.md",
        content="# Example\n\n<!-- include-file(snippet.md) -->\n[guide](<guide(.md>)\n",
        include_options=IncludeOptions(render_mode="raw"),
    )
    document.process_tags()
    document.content = move_base_path_in_md_text(document.content or "", "guides")
    document.beautify()
    document.write()
    assert search_link_in_md_text(document.content or "")[0]["url"] == "guides/guide(.md"

    client = TranslationClient(transport=offline_translation)
    translated = translate_md(document.content or "", client=client, segmentation="paragraph")
    (output / "translated.md").write_text(translated, encoding="utf-8")
    print(convert_md_to_html(output / "document.md"))
    if args.pdf:
        print(
            convert_md_to_pdf(
                output / "document.md",
                options=PdfOptions(timeout=60),
                features=PdfFeatures(metadata={"Title": "pymdtools example"}),
            )
        )


if __name__ == "__main__":
    main()
