"""MyMemory HTTP transport and provider-specific segment limits."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any, cast
from urllib.parse import urlencode
from urllib.request import urlopen

MYMEMORY_ENDPOINT = "https://api.mymemory.translated.net/get"

MYMEMORY_MAX_QUERY_BYTES = 500


def utf8_len(text: str) -> int:
    """
    Return the UTF-8 byte length of a string.

    Args:
        text: Text to measure.

    Returns:
        Number of bytes used by the UTF-8 representation.
    """
    return len(text.encode("utf-8"))


def split_oversized_word(word: str, max_bytes: int) -> list[str]:
    """
    Split one word into chunks accepted by MyMemory.

    Args:
        word: Word that may exceed ``max_bytes`` once UTF-8 encoded.
        max_bytes: Maximum UTF-8 byte length per chunk.

    Returns:
        Chunks whose UTF-8 byte length is at most ``max_bytes``.
    """
    chunks: list[str] = []
    current = ""
    for char in word:
        candidate = current + char
        if current and utf8_len(candidate) > max_bytes:
            chunks.append(current)
            current = char
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def split_text_for_mymemory(text: str, max_bytes: int = MYMEMORY_MAX_QUERY_BYTES) -> list[str]:
    """
    Split text into UTF-8 chunks compatible with MyMemory.

    The function keeps whitespace in the emitted chunks so joining translated
    chunks does not silently remove source spacing.

    Args:
        text: Source text to split.
        max_bytes: Maximum UTF-8 byte length per chunk.

    Returns:
        Ordered chunks to send to MyMemory.

    Raises:
        ValueError: If ``max_bytes`` is smaller than one byte.
    """
    if max_bytes < 1:
        raise ValueError("max_bytes must be greater than zero")
    if text == "":
        return []

    chunks: list[str] = []
    current = ""

    for part in re.findall(r"\s+|\S+", text):
        candidate = current + part
        if utf8_len(candidate) <= max_bytes:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if utf8_len(part) <= max_bytes:
            current = part
            continue

        split_part = split_oversized_word(part, max_bytes)
        chunks.extend(split_part[:-1])
        current = split_part[-1]

    chunks.append(current)
    return chunks


def build_mymemory_url(
    text: str,
    src: str,
    dest: str,
    *,
    email: str | None,
    api_key: str | None,
) -> str:
    """
    Build a MyMemory ``/get`` request URL.

    Args:
        text: Source text segment.
        src: Source language code.
        dest: Destination language code.
        email: Optional contact email sent as ``de``.
        api_key: Optional MyMemory private key.

    Returns:
        Fully encoded MyMemory URL.
    """
    parameters = {
        "q": text,
        "langpair": f"{src}|{dest}",
    }
    if email:
        parameters["de"] = email
    if api_key:
        parameters["key"] = api_key
    return f"{MYMEMORY_ENDPOINT}?{urlencode(parameters)}"


def extract_mymemory_translation(payload: Mapping[str, Any]) -> str:
    """
    Extract translated text from a MyMemory JSON payload.

    Args:
        payload: Decoded MyMemory response.

    Returns:
        Translated text.

    Raises:
        RuntimeError: If MyMemory reports an error or the response shape is
            incomplete.
    """
    status = payload.get("responseStatus")
    if isinstance(status, int) and status >= 400:
        detail = payload.get("responseDetails", "unknown MyMemory error")
        raise RuntimeError(str(detail))

    response_data_obj = payload.get("responseData")
    if not isinstance(response_data_obj, Mapping):
        raise RuntimeError("Missing MyMemory responseData")
    response_data = cast(Mapping[str, object], response_data_obj)

    translated_text = response_data.get("translatedText")
    if not isinstance(translated_text, str):
        raise RuntimeError("Missing MyMemory translatedText")
    return translated_text


def request_mymemory_translation(
    text: str,
    src: str,
    dest: str,
    *,
    email: str | None,
    api_key: str | None,
    timeout: float,
) -> str:
    """
    Request one translation segment from MyMemory.

    Args:
        text: Source text segment. Must fit MyMemory's request size limit.
        src: Source language code.
        dest: Destination language code.
        email: Optional contact email sent as ``de``.
        api_key: Optional MyMemory private key.
        timeout: Network timeout in seconds.

    Returns:
        Translated text segment.
    """
    url = build_mymemory_url(text, src, dest, email=email, api_key=api_key)
    with urlopen(url, timeout=timeout) as response:  # noqa: S310 - URL is fixed to MyMemory.
        payload: object = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise RuntimeError("Invalid MyMemory response: expected a JSON object")
    return extract_mymemory_translation(cast(Mapping[str, Any], payload))
