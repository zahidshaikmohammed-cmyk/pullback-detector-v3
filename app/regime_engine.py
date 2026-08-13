from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Sequence

from .market_structure_engine import CandleLike


@dataclass(frozen=True)
class RegimeResult:
    regime: str
    confidence: float
    range_width: float
    directional_efficiency: float


def classify_regime(candles: Sequence[CandleLike], lookback: int = 12) -> RegimeResult:
    """Classify price behaviour without producing a trade signal.

    Sideways is favoured when price remains compressed relative to its typical
    movement and directional efficiency is low. Transitional is returned when
    compression is present but directional movement is beginning to dominate.
    """
    if len(candles) < max(3, lookback):
        return RegimeResult("unknown", 0.0, 0.0, 0.0)

    window = candles[-lookback:]
    closes = [float(c.close) for c in window]
    highs = [float(c.high) for c in window]
    lows = [float(c.low) for c in window]

    total_range = max(highs) - min(lows)
    net_move = abs(closes[-1] - closes[0])
    moves = sum(abs(closes[i] - closes[i - 1]) for i in range(1, len(closes)))
    efficiency = net_move / moves if moves else 0.0

    average_range = mean(h - l for h, l in zip(highs, lows))
    normalized_width = total_range / average_range if average_range else 0.0

    # Conservative thresholds: the regime engine is a gate, not an optimizer.
    if efficiency <= 0.30 and normalized_width <= 5.0:
        confidence = min(1.0, 0.5 + (0.30 - efficiency) + max(0.0, 5.0 - normalized_width) / 10)
        return RegimeResult("sideways", confidence, total_range, efficiency)

    if efficiency <= 0.55:
        confidence = max(0.0, 1.0 - efficiency)
        return RegimeResult("transitional", confidence, total_range, efficiency)

    return RegimeResult("directional", min(1.0, efficiency), total_range, efficiency)
