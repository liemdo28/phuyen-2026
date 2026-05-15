from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class ProviderSignal:
    provider: str
    category: str
    score: float
    summary: str
    metadata: dict[str, object] = field(default_factory=dict)


class RealtimeProvider(Protocol):
    async def collect(self, context_text: str, now: datetime) -> list[ProviderSignal]: ...


class HeuristicWeatherProvider:
    async def collect(self, context_text: str, now: datetime) -> list[ProviderSignal]:
        text = context_text.lower()
        signals: list[ProviderSignal] = []
        if any(token in text for token in ["mưa", "giông", "nắng", "nóng", "thời tiết"]):
            signals.append(
                ProviderSignal(
                    provider="heuristic_weather",
                    category="weather",
                    score=0.55,
                    summary="Detected weather-sensitive conversation context.",
                )
            )
        return signals


class HeuristicTrafficProvider:
    async def collect(self, context_text: str, now: datetime) -> list[ProviderSignal]:
        text = context_text.lower()
        score = 0.0
        if any(token in text for token in ["kẹt xe", "traffic", "grab", "taxi", "di chuyển"]):
            score += 0.45
        if 17 <= now.hour <= 19:
            score += 0.2
        if score <= 0:
            return []
        return [
            ProviderSignal(
                provider="heuristic_traffic",
                category="traffic",
                score=min(score, 1.0),
                summary="Detected traffic-sensitive timing or transport context.",
            )
        ]


class ProviderRegistry:
    def __init__(self) -> None:
        self.providers: list[RealtimeProvider] = [
            HeuristicWeatherProvider(),
            HeuristicTrafficProvider(),
        ]

    async def collect(self, context_text: str, now: datetime) -> list[ProviderSignal]:
        collected: list[ProviderSignal] = []
        for provider in self.providers:
            collected.extend(await provider.collect(context_text, now))
        return collected
