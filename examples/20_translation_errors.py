"""Handle transient failures, fallback text and damaged Markdown translation markers."""

import logging
import sys

from _support import output_directory

from pymdtools.translate import (
    TranslationClient,
    TranslationStructureError,
    translate_md,
    translate_txt,
)


def main() -> None:
    output = output_directory(__file__, __doc__)
    logging.basicConfig(stream=sys.stdout, format="Demo log: %(message)s")
    attempts = 0

    def intermittent(text: str, src: str, dest: str, **kwargs: object) -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError("Simulated transient failure")
        return "Hello"

    client = TranslationClient(intermittent, max_retries=1, retry_delay=0)
    assert translate_txt("Bonjour", client=client, on_error="raise") == "Hello"
    assert attempts == 2

    def unavailable(text: str, src: str, dest: str, **kwargs: object) -> str:
        raise TimeoutError("Simulated unavailable service")

    fallback = translate_txt(
        "Keep this text",
        client=TranslationClient(unavailable, max_retries=0),
        on_error="keep_original",
    )
    assert fallback == "Keep this text"
    broken = TranslationClient(lambda text, src, dest, **kwargs: "Markers were lost")
    try:
        translate_md("A **bold** word", client=broken, segmentation="paragraph", on_error="raise")
    except TranslationStructureError:
        message = "The invalid translation was rejected; the original document is available."
    else:
        raise AssertionError("The provider response should have failed structural validation")
    (output / "error-handling.txt").write_text(f"{fallback}\n{message}\n", encoding="utf-8")
    print("Expected failures handled locally; no service was contacted.")


if __name__ == "__main__":
    main()
