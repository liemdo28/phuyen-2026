from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class SemanticMemoryItem:
    namespace: str
    key: str
    text: str
    metadata: dict[str, object]


class VectorMemoryBackend(Protocol):
    async def upsert(self, item: SemanticMemoryItem) -> None: ...

    async def similar(self, namespace: str, query: str, limit: int = 5) -> list[SemanticMemoryItem]: ...


class InMemoryVectorBackend:
    def __init__(self) -> None:
        self._items: list[SemanticMemoryItem] = []

    async def upsert(self, item: SemanticMemoryItem) -> None:
        self._items = [existing for existing in self._items if not (existing.namespace == item.namespace and existing.key == item.key)]
        self._items.append(item)

    async def similar(self, namespace: str, query: str, limit: int = 5) -> list[SemanticMemoryItem]:
        query_tokens = set(query.lower().split())
        scored: list[tuple[int, SemanticMemoryItem]] = []
        for item in self._items:
            if item.namespace != namespace:
                continue
            overlap = len(query_tokens.intersection(item.text.lower().split()))
            scored.append((overlap, item))
        return [item for score, item in sorted(scored, key=lambda pair: pair[0], reverse=True)[:limit] if score > 0]


class SemanticMemoryService:
    def __init__(self, backend: VectorMemoryBackend | None = None) -> None:
        self.backend = backend or InMemoryVectorBackend()

    async def remember(self, namespace: str, key: str, text: str, metadata: dict[str, object]) -> None:
        await self.backend.upsert(SemanticMemoryItem(namespace=namespace, key=key, text=text, metadata=metadata))

    async def recall(self, namespace: str, query: str, limit: int = 5) -> list[SemanticMemoryItem]:
        return await self.backend.similar(namespace, query, limit=limit)
