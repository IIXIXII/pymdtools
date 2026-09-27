"""Public translation client; implementation is independent of translate.py."""

from ._translation.client import TranslationClient as TranslationClient
from ._translation.client import TranslationTransport as TranslationTransport

__all__ = ["TranslationClient", "TranslationTransport"]
