from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .anatomy_engine import Anatomy, detect_anatomies
from .confirmation_engine import ConfirmationResult
from .entry_engine import EntryPlan, engineer_entry
from .real_confirmation_adapter import derive_confirmation
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
    """Execute V3 with completed-candle confirmation and strict downstream gating."""
    regime = classify_regime(candles)
    anatomies = detect_anatomies(candles, location) if regime.regime in {"sideways", "transitional"} else []

    confirmations: list[ConfirmationResult] = []
    selected: Anatomy | None = None
    for anatomy in anatomies:
        result = derive_confirmation(candles, anatomy)
        confirmations.append(result)
        if result.confirmed:
            selected = anatomy
            break

    confirmation = confirmations[-1] if confirmations else None
    signal = generate_signal(selected, confirmation, regime.regime) if confirmation else None
    entry = engineer_entry(signal) if signal else None
    return PipelineResult(regime, anatomies, confirmations, signal, entry)
