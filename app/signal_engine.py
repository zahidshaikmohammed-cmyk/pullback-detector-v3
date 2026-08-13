from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .confirmation_engine import ConfirmationResult
from .anatomy_engine import Anatomy


@dataclass(frozen=True)
class Signal:
    direction: str
    anatomy: str
    trigger_level: float
    invalidation_level: float
    confidence: float


def generate_signal(
    anatomy: Optional[Anatomy],
    confirmation: ConfirmationResult,
    regime: str,
) -> Optional[Signal]:
    """Create a signal only after all structural gates pass."""
    if anatomy is None or not confirmation.confirmed:
        return None
    if regime not in {"sideways", "transitional"}:
        return None

    confidence = min(1.0, anatomy.confidence * (confirmation.score / 4.0))
    return Signal(
        direction=anatomy.direction,
        anatomy=anatomy.kind,
        trigger_level=anatomy.trigger_level,
        invalidation_level=anatomy.invalidation_level,
        confidence=confidence,
    )
