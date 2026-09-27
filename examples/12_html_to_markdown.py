"""Convert an HTML article to Markdown with explicit heading and list styles."""

from _support import DATA, output_directory

from pymdtools.markdownify_integration import markdownify


def main() -> None:
    output = output_directory(__file__, __doc__)
    html = (DATA / "article.html").read_text(encoding="utf-8")
    markdown = markdownify(html, heading_style="ATX", bullets="-")
    assert markdown.startswith("# A small HTML article")
    assert "[Read the guide](https://example.com/guide)" in markdown
    (output / "article.md").write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
