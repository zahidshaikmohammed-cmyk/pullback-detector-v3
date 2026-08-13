from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable

from .data_validation import ValidationResult, validate_candle


@dataclass(frozen=True)
class Candle:
    instrument: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketDataIngestion:
    """Transport-neutral ingestion boundary for live and replay data."""

    def __init__(self, validator: Callable[..., ValidationResult] = validate_candle) -> None:
        self._validator = validator
        self._seen: set[tuple[str, datetime]] = set()
        self._last_timestamp: dict[str, datetime] = {}

    def ingest(self, candles: Iterable[Candle]) -> list[Candle]:
        accepted: list[Candle] = []
        for candle in candles:
            key = (candle.instrument, candle.timestamp)
            if key in self._seen:
                continue

            result = self._validator(
                candle.timestamp,
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
            )
            if not result.valid:
                continue

            previous = self._last_timestamp.get(candle.instrument)
            if previous is not None and candle.timestamp <= previous:
                continue

            self._seen.add(key)
            self._last_timestamp[candle.instrument] = candle.timestamp
            accepted.append(candle)

        return accepted

    def reset(self) -> None:
        self._seen.clear()
        self._last_timestamp.clear()
