from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class CandleLike:
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(frozen=True)
class StructureResult:
    trend: str
    swing_high: float | None
    swing_low: float | None
    range_high: float | None
    range_low: float | None


def analyze_structure(candles: Sequence[CandleLike]) -> StructureResult:
    if len(candles) < 3:
        return StructureResult("unknown", None, None, None, None)
    highs = [float(c.high) for c in candles]
    lows = [float(c.low) for c in candles]
    closes = [float(c.close) for c in candles]
    trend = "neutral"
    if closes[-1] > closes[0]:
        trend = "bullish"
    elif closes[-1] < closes[0]:
        trend = "bearish"
    return StructureResult(trend, max(highs), min(lows), max(highs), min(lows))
