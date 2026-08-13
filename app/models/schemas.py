"""Canonical V3 schemas. Detection logic will be added after schema tests."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass(frozen=True)
class Candle:
    instrument_id: str
    timeframe: str
    start: datetime
    end: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    complete: bool

@dataclass(frozen=True)
class MarketRegime:
    timestamp: datetime
    regime: str
    strength: float | None = None
    range_high: float | None = None
    range_low: float | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Signal:
    signal_id: str
    anatomy_id: str
    timestamp: datetime
    direction: str
    trigger_price: float
    invalidation: float
    evidence_snapshot: dict[str, Any] = field(default_factory=dict)
