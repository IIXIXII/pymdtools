"""Translate plain text with an offline transport and demonstrate the client cache."""

import json

from _support import output_directory

from pymdtools.translate import TranslationClient, translate_txt


def main() -> None:
    output = output_directory(__file__, __doc__)
    calls = []

    def local_transport(text: str, src: str, dest: str, **kwargs: object) -> str:
        """A tiny dictionary for demonstration, not a general translation engine."""
        calls.append({"text": text, "src": src, "dest": dest})
        return {"Bonjour": "Hello", "Merci": "Thank you"}.get(text, text)

    client = TranslationClient(transport=local_transport, cache_size=8)
    first = translate_txt("Bonjour", src="fr", dest="en", client=client)
    second = translate_txt("Bonjour", src="fr", dest="en", client=client)
    assert first == second == "Hello" and len(calls) == 1
    client.clear_cache()
    translate_txt("Bonjour", src="fr", dest="en", client=client)
    assert len(calls) == 2
    (output / "transport-calls.json").write_text(json.dumps(calls, indent=2), encoding="utf-8")
    print("Three translation calls, two transport calls, no network requests.")


if __name__ == "__main__":
    main()
