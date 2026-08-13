from __future__ import annotations

from dataclasses import dataclass

from .signal_engine import Signal


@dataclass(frozen=True)
class EntryPlan:
    direction: str
    entry: float
    invalidation: float
    model: str


def engineer_entry(signal: Signal, model: str = "retest") -> EntryPlan | None:
    """Translate an accepted structural signal into a deterministic entry plan."""
    if model not in {"retest", "displacement", "reclaim"}:
        return None
    if signal.direction == "long" and signal.trigger_level <= signal.invalidation_level:
        return None
    if signal.direction == "short" and signal.trigger_level >= signal.invalidation_level:
        return None

    return EntryPlan(
        direction=signal.direction,
        entry=signal.trigger_level,
        invalidation=signal.invalidation_level,
        model=model,
    )
