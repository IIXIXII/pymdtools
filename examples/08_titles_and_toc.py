"""Change heading style and export an HTML table of contents."""

from _support import DATA, output_directory

from pymdtools.instruction import get_title_from_md_text, set_title_in_md_text
from pymdtools.mdfile import MarkdownContent


def main() -> None:
    output = output_directory(__file__, __doc__)
    source = (DATA / "document.md").read_text(encoding="utf-8")
    print("Original title:", get_title_from_md_text(source))
    preserved = set_title_in_md_text(source, "My handbook", style="preserve")
    atx = set_title_in_md_text(source, "My handbook", style="atx")
    (output / "setext.md").write_text(preserved, encoding="utf-8")
    (output / "atx.md").write_text(atx, encoding="utf-8")
    toc = MarkdownContent(content=atx).toc  # An HTML fragment, not a Markdown list.
    (output / "toc.html").write_text(
        '<!doctype html><meta charset="utf-8">\n' + toc, encoding="utf-8"
    )
    assert 'href="#installation"' in toc
    print("Title variants and toc.html:", output)


if __name__ == "__main__":
    main()
