"""Injectable translation transport with bounded retries and an in-memory cache."""

from __future__ import annotations

import math
import time
from abc import abstractmethod
from collections import OrderedDict
from typing import Protocol
from urllib.error import HTTPError, URLError

from . import mymemory


class TranslationTransport(Protocol):
    """Translate one segment; raise an exception when no translation is available."""

    @abstractmethod
    def __call__(
        self,
        text: str,
        src: str,
        dest: str,
        *,
        email: str | None,
        api_key: str | None,
        timeout: float,
    ) -> str:
        raise NotImplementedError


class TranslationClient:
    """Reusable client scoped to one caller, with no global or persistent cache.

    Defaults to MyMemory. Inject ``transport`` to use an offline implementation
    or another provider. Only successful responses are cached. HTTP 429/5xx and
    network timeouts may be retried; each attempt uses the supplied timeout.
    Instances are intended for sequential use. Call ``clear_cache`` to discard
    retained text and credentials, or set ``cache_size=0`` to disable caching.
    """

    def __init__(
        self,
        transport: TranslationTransport | None = None,
        *,
        cache_size: int = 128,
        max_retries: int = 2,
        retry_delay: float = 0.25,
    ) -> None:
        if cache_size < 0:
            raise ValueError("cache_size must be non-negative")
        if not 0 <= max_retries <= 5:
            raise ValueError("max_retries must be between zero and five")
        if not math.isfinite(retry_delay) or not 0 <= retry_delay <= 10:
            raise ValueError("retry_delay must be finite and between zero and ten seconds")
        if transport is None:
            transport = mymemory.request_mymemory_translation
        self._transport = transport
        self._cache_size = cache_size
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._cache: OrderedDict[tuple[str, str, str, str | None, str | None], str] = OrderedDict()

    def clear_cache(self) -> None:
        """Discard all translations retained by this client."""
        self._cache.clear()

    def translate(
        self,
        text: str,
        src: str,
        dest: str,
        *,
        email: str | None,
        api_key: str | None,
        timeout: float,
    ) -> str:
        """Translate a segment, retry transient failures, and cache successes."""
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and greater than zero")
        key = (text, src, dest, email, api_key)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        attempt = 0
        while True:
            try:
                result = self._transport(
                    text, src, dest, email=email, api_key=api_key, timeout=timeout
                )
                break
            except (URLError, TimeoutError) as exc:
                transient = not isinstance(exc, HTTPError) or exc.code in {429, 500, 502, 503, 504}
                if not transient or attempt >= self._max_retries:
                    raise
                if isinstance(exc, HTTPError):
                    exc.close()
                time.sleep(self._retry_delay * 2**attempt)
                attempt += 1
        if self._cache_size:
            self._cache[key] = result
            if len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
        return result
