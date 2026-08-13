from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reason: str


def validate_timestamp(timestamp: datetime, now: datetime | None = None) -> ValidationResult:
    if timestamp.tzinfo is None:
        return ValidationResult(False, "timestamp must be timezone-aware")
    reference = now or datetime.now(timezone.utc)
    if timestamp > reference:
        return ValidationResult(False, "future timestamp")
    return ValidationResult(True, "ok")


def validate_ohlc(open_: float, high: float, low: float, close: float) -> ValidationResult:
    values = (open_, high, low, close)
    if not all(isinstance(value, (int, float)) and isfinite(value) for value in values):
        return ValidationResult(False, "non-finite OHLC value")
    if high < low:
        return ValidationResult(False, "high below low")
    if not (low <= open_ <= high and low <= close <= high):
        return ValidationResult(False, "OHLC value outside candle range")
    return ValidationResult(True, "ok")


def validate_volume(volume: float) -> ValidationResult:
    if not isinstance(volume, (int, float)) or not isfinite(volume):
        return ValidationResult(False, "invalid volume")
    if volume < 0:
        return ValidationResult(False, "negative volume")
    return ValidationResult(True, "ok")


def validate_candle(
    timestamp: datetime,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float,
    now: datetime | None = None,
) -> ValidationResult:
    checks = (
        validate_timestamp(timestamp, now),
        validate_ohlc(open_, high, low, close),
        validate_volume(volume),
    )
    for result in checks:
        if not result.valid:
            return result
    return ValidationResult(True, "ok")
