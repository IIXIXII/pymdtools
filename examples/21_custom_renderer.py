"""Extend the Mistune HTML renderer with a final footer using the close hook."""

from _support import output_directory

from pymdtools.mistune_integration import ClosingHTMLRenderer, create_markdown_with_close


class FooterRenderer(ClosingHTMLRenderer):
    def close(self) -> str:
        return "<footer>Generated locally with pymdtools.</footer>\n"


def main() -> None:
    output = output_directory(__file__, __doc__)
    render = create_markdown_with_close(renderer=FooterRenderer())
    fragment = render("# Custom renderer\n\nA **formatted** paragraph.\n")
    assert fragment.endswith("<footer>Generated locally with pymdtools.</footer>\n")
    page = output / "custom.html"
    page.write_text('<!doctype html><meta charset="utf-8">\n' + fragment, encoding="utf-8")
    print("Open:", page)


if __name__ == "__main__":
    main()
