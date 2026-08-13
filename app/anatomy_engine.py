from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Anatomy:
    kind: str
    direction: str
    start_index: int
    end_index: int
    trigger_level: float
    invalidation_level: float
    confidence: float


def detect_anatomies(candles: Sequence, location: str) -> list[Anatomy]:
    """Detect structural pullback anatomies near meaningful range locations.

    This layer identifies candidates only. Confirmation and signal engines decide
    whether a candidate is actionable.
    """
    if len(candles) < 3 or location == "mid_range":
        return []

    out: list[Anatomy] = []
    a, b, c = candles[-3:]

    # Sweep-and-reclaim: final candle returns through the prior extreme.
    if location == "lower_boundary" and b.low < a.low and c.close > b.high:
        out.append(Anatomy("sweep_reclaim", "long", len(candles)-3, len(candles)-1,
                           c.high, b.low, 0.75))
    elif location == "upper_boundary" and b.high > a.high and c.close < b.low:
        out.append(Anatomy("sweep_reclaim", "short", len(candles)-3, len(candles)-1,
                           c.low, b.high, 0.75))

    # Failed auction: excursion beyond a boundary followed by decisive return.
    if location == "lower_boundary" and b.low < a.low and c.close > a.low:
        out.append(Anatomy("failed_auction", "long", len(candles)-3, len(candles)-1,
                           a.low, b.low, 0.65))
    elif location == "upper_boundary" and b.high > a.high and c.close < a.high:
        out.append(Anatomy("failed_auction", "short", len(candles)-3, len(candles)-1,
                           a.high, b.high, 0.65))

    return out
