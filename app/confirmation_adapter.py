from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ConfirmationEvidence:
    structure_intact: bool
    retest_valid: bool
    response_valid: bool
    displacement_valid: bool


def evaluate(candles: Sequence, direction: str, trigger_level: float, invalidation_level: float) -> ConfirmationEvidence:
    """Derive confirmation evidence directly from completed candles.

    Conservative by design: insufficient evidence returns false gates rather than
    inventing confirmation. No future candles are inspected.
    """
    if len(candles) < 3 or direction not in {"long", "short"}:
        return ConfirmationEvidence(False, False, False, False)

    a, b, c = candles[-3:]
    if direction == "long":
        structure = min(b.low, c.low) > invalidation_level
        retest = b.low <= trigger_level <= b.high
        response = c.close > b.close and c.close > trigger_level
        displacement = (c.close - c.open) > (b.high - b.low) * 0.25
    else:
        structure = max(b.high, c.high) < invalidation_level
        retest = b.low <= trigger_level <= b.high
        response = c.close < b.close and c.close < trigger_level
        displacement = (c.open - c.close) > (b.high - b.low) * 0.25

    return ConfirmationEvidence(structure, retest, response, displacement)
