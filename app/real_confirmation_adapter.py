from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .anatomy_engine import Anatomy
from .confirmation_engine import ConfirmationResult, confirm_pullback


@dataclass(frozen=True)
class ConfirmationEvidence:
    structure_intact: bool
    retest_valid: bool
    response_valid: bool
    displacement_valid: bool


def _body(c) -> float:
    return abs(float(c.close) - float(c.open))


def _range(c) -> float:
    return max(float(c.high) - float(c.low), 0.0)


def _close_location(c, direction: str) -> bool:
    span = _range(c)
    if span == 0:
        return False
    if direction == "long":
        return (float(c.close) - float(c.low)) / span >= 0.65
    return (float(c.high) - float(c.close)) / span >= 0.65


def derive_confirmation(candles: Sequence, anatomy: Anatomy) -> ConfirmationResult:
    """Derive confirmation from completed candles only; never auto-confirm."""
    if len(candles) < 4:
        return confirm_pullback(
            structure_intact=False,
            retest_valid=False,
            response_valid=False,
            displacement_valid=False,
        )

    previous = candles[-3]
    response = candles[-2]
    latest = candles[-1]
    direction = anatomy.direction
    trigger = float(anatomy.trigger_level)
    invalidation = float(anatomy.invalidation_level)

    if direction == "long":
        structure = min(float(response.low), float(latest.low)) > invalidation
        retest = float(latest.low) <= trigger and float(latest.close) > trigger
        response_valid = float(response.close) > float(response.open) and _close_location(response, direction)
        reference_body = max(_body(previous), _range(previous) * 0.25)
        displacement = _body(response) >= reference_body * 1.15 and float(response.close) > float(previous.high)
    else:
        structure = max(float(response.high), float(latest.high)) < invalidation
        retest = float(latest.high) >= trigger and float(latest.close) < trigger
        response_valid = float(response.close) < float(response.open) and _close_location(response, direction)
        reference_body = max(_body(previous), _range(previous) * 0.25)
        displacement = _body(response) >= reference_body * 1.15 and float(response.close) < float(previous.low)

    return confirm_pullback(
        structure_intact=structure,
        retest_valid=retest,
        response_valid=response_valid,
        displacement_valid=displacement,
    )
