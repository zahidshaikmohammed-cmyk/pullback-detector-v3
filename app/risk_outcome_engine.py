from __future__ import annotations

from dataclasses import dataclass

from .entry_engine import EntryPlan


@dataclass(frozen=True)
class RiskOutcome:
    risk_distance: float
    target: float
    reward_distance: float
    reward_risk: float
    valid: bool


def evaluate(entry: EntryPlan, target: float) -> RiskOutcome:
    risk_distance = abs(entry.entry - entry.invalidation)
    reward_distance = abs(target - entry.entry)
    reward_risk = reward_distance / risk_distance if risk_distance else 0.0
    return RiskOutcome(
        risk_distance=risk_distance,
        target=target,
        reward_distance=reward_distance,
        reward_risk=reward_risk,
        valid=risk_distance > 0 and reward_risk >= 1.5,
    )
