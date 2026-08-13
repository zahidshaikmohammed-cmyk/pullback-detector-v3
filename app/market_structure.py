from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .market_data_ingestion import Candle


@dataclass(frozen=True)
class SwingPoint:
    index: int
    timestamp: object
    price: float
    kind: str


@dataclass(frozen=True)
class StructureSnapshot:
    trend: str
    swing_high: SwingPoint | None
    swing_low: SwingPoint | None
    range_high: float | None
    range_low: float | None
    range_width: float | None


class MarketStructureEngine:
    """Deterministic price-structure extraction; it does not issue signals."""

    def __init__(self, swing_lookback: int = 2) -> None:
        if swing_lookback < 1:
            raise ValueError("swing_lookback must be >= 1")
        self.swing_lookback = swing_lookback

    def swings(self, candles: Sequence[Candle]) -> list[SwingPoint]:
        n = self.swing_lookback
        points: list[SwingPoint] = []
        for i in range(n, len(candles) - n):
            current = candles[i]
            left = candles[i - n : i]
            right = candles[i + 1 : i + n + 1]
            if current.high > max(c.high for c in left + right):
                points.append(SwingPoint(i, current.timestamp, current.high, "high"))
            if current.low < min(c.low for c in left + right):
                points.append(SwingPoint(i, current.timestamp, current.low, "low"))
        return points

    def snapshot(self, candles: Sequence[Candle]) -> StructureSnapshot:
        if not candles:
            return StructureSnapshot("unknown", None, None, None, None, None)

        points = self.swings(candles)
        highs = [p for p in points if p.kind == "high"]
        lows = [p for p in points if p.kind == "low"]
        latest_high = highs[-1] if highs else None
        latest_low = lows[-1] if lows else None

        window = candles[-max(2 * self.swing_lookback + 1, 5) :]
        range_high = max(c.high for c in window)
        range_low = min(c.low for c in window)
        width = range_high - range_low

        trend = "neutral"
        if len(highs) >= 2 and len(lows) >= 2:
            hh = highs[-1].price > highs[-2].price
            hl = lows[-1].price > lows[-2].price
            lh = highs[-1].price < highs[-2].price
            ll = lows[-1].price < lows[-2].price
            if hh and hl:
                trend = "bullish"
            elif lh and ll:
                trend = "bearish"

        return StructureSnapshot(trend, latest_high, latest_low, range_high, range_low, width)
