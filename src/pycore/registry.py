"""Generic typed registry — decorator-based auto-registration and dispatch."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class Registry:
    """A registry that stores instances by name with decorator registration.

    Usage:
        fetchers = Registry("fetcher")

        @fetchers.register
        class JinaFetcher:
            name = "jina"
            def can_handle(self, url): return url.startswith("http")
            def fetch(self, url): ...

        # Lookup
        fetchers.get("jina")
        fetchers.all()
        fetchers.find(lambda f: f.can_handle(url))
        fetchers.names()
    """

    def __init__(self, kind: str) -> None:
        self._kind = kind
        self._items: dict[str, Any] = {}
        self._ordered: list[Any] = []

    def register(self, cls: type[T]) -> type[T]:
        """Decorator to register a class. Instantiates and stores it."""
        instance = cls()
        name = getattr(instance, "name", cls.__name__)
        self._items[name] = instance
        self._ordered.append(instance)
        return cls

    def get(self, name: str) -> Any | None:
        """Get a registered instance by name."""
        return self._items.get(name)

    def all(self) -> list[Any]:
        """Get all registered instances in registration order."""
        return list(self._ordered)

    def names(self) -> list[str]:
        """Get all registered names."""
        return list(self._items.keys())

    def find(self, predicate: Callable[[Any], bool]) -> Any | None:
        """Find the first item matching a predicate."""
        for item in self._ordered:
            if predicate(item):
                return item
        return None

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, name: str) -> bool:
        return name in self._items
