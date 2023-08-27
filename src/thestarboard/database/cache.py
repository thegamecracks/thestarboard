import time
from abc import abstractmethod
from typing import Any, Protocol, Self


class CacheSet(Protocol):
    """An interface for caching unique keys into buckets.

    Implementations should support the asynchronous context manager protocol.

    Usage::

        async with CacheSet() as cache:
            await cache.add("foo", "bar")
            if await cache.exists("foo", "bar"):
                await cache.discard("foo", "bar")

    """

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb, /):
        return

    @abstractmethod
    async def add(self, key: str) -> Any:
        """Adds the given key to the set."""

    @abstractmethod
    async def discard(self, key: str) -> Any:
        """Discards the given key from the set.

        This should be a no-op if the key is not present.

        """

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Checks the set has the given key."""


class ExpiringMemoryCacheSet(CacheSet):
    """Implements an in-memory cache set with expiring entries.

    Parameters
    ----------
    expires_after: float
        The amount of time in seconds before an entry expires.

    """

    def __init__(self, *, expires_after: float) -> None:
        self.expires_after = expires_after
        self._key_expirations: dict[str, float] = {}
        self._next_integrity_check: float = self._time()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._key_expirations.clear()

    def _time(self) -> float:
        return time.monotonic()

    def _verify_integrity(self, now: float) -> None:
        if now < self._next_integrity_check:
            return

        self._next_integrity_check = now + self.expires_after

        to_remove = []
        for key, expiration in self._key_expirations.items():
            if expiration >= now:
                to_remove.append(key)

        for key in to_remove:
            self._key_expirations.pop(key)

    async def add(self, key: str) -> None:
        now = self._time()
        self._verify_integrity(now)
        if not await self.exists(key):
            self._key_expirations[key] = now + self.expires_after

    async def discard(self, key: str) -> None:
        self._key_expirations.pop(key, None)

    async def exists(self, key: str) -> bool:
        expiration = self._key_expirations.get(key)
        return expiration is not None and expiration < self._time()
