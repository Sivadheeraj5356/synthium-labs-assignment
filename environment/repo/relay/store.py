"""Idempotency helpers for ingest requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class StoreResult:
    delivered: bool
    replayed: bool
    value: object | None = None


class IdempotencyStore:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def process(self, key: str, deliver_fn: Callable[[], T]) -> StoreResult:
        value = deliver_fn()
        self._seen.add(key)
        return StoreResult(delivered=True, replayed=False, value=value)

    def has(self, key: str) -> bool:
        return key in self._seen
