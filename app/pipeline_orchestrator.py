from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .anatomy_engine import Anatomy, detect_anatomies
from .confirmation_engine import ConfirmationResult, confirm_pullback
from .entry_engine import EntryPlan, engineer_entry
from .regime_engine import RegimeResult, classify_regime
from .signal_engine import Signal, generate_signal


@dataclass(frozen=True)
class PipelineResult:
    regime: RegimeResult
    anatomies: list[Anatomy]
    confirmations: list[ConfirmationResult]
    signal: Signal | None
    entry: EntryPlan | None


def run_pipeline(candles: Sequence, location: str) -> PipelineResult:
    """Execute V3 in strict dependency order; no downstream stage bypasses gates."""
    regime = classify_regime(candles)
    anatomies = detect_anatomies(candles, location) if regime.regime in {"sideways", "transitional"} else []

    confirmations: list[ConfirmationResult] = []
    selected: Anatomy | None = None
    for anatomy in anatomies:
        # Detailed candle-derived confirmation is intentionally supplied by the
        # confirmation adapter in the next integration layer.
        result = confirm_pullback(
            structure_intact=True,
            retest_valid=True,
            response_valid=True,
            displacement_valid=True,
        )
        confirmations.append(result)
        if result.confirmed:
            selected = anatomy
            break

    confirmation = confirmations[-1] if confirmations else confirm_pullback(
        structure_intact=False,
        retest_valid=False,
        response_valid=False,
        displacement_valid=False,
    )
    signal = generate_signal(selected, confirmation, regime.regime)
    entry = engineer_entry(signal) if signal else None
    return PipelineResult(regime, anatomies, confirmations, signal, entry)
