"""Translate paragraph text offline while preserving links, formatting and code."""

from _support import output_directory

from pymdtools.mdcommon import search_link_in_md_text
from pymdtools.translate import TranslationClient, translate_md


def main() -> None:
    output = output_directory(__file__, __doc__)
    sent = []

    def local_transport(text: str, src: str, dest: str, **kwargs: object) -> str:
        sent.append(text)
        # Retain all protected markers inserted by paragraph segmentation.
        return (
            text.replace("Bonjour", "Hello").replace("monde", "world").replace("guide", "handbook")
        )

    source = (
        "# Bonjour\n\nBonjour **monde**, lire le [guide](private-guide.md).\n\n"
        "```python\nprint('Bonjour')\n```\n"
    )
    result = translate_md(
        source,
        src="fr",
        dest="en",
        client=TranslationClient(transport=local_transport),
        segmentation="paragraph",
        on_error="raise",
    )
    assert search_link_in_md_text(result)[0]["url"] == "private-guide.md"
    assert "print('Bonjour')" in result
    assert all("private-guide.md" not in text for text in sent)
    (output / "source.md").write_text(source, encoding="utf-8")
    (output / "translated.md").write_text(result, encoding="utf-8")
    print("Translated visible text; destinations and code stayed local:", output)


if __name__ == "__main__":
    main()
