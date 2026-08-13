from __future__ import annotations

from math import isfinite


class DataValidationError(ValueError):
    """Raised when market data violates V3 validation rules."""


def validate_ohlc(open_: float, high: float, low: float, close: float) -> None:
    values = (open_, high, low, close)
    if not all(isinstance(value, (int, float)) and isfinite(value) for value in values):
        raise DataValidationError("non-finite OHLC value")
    if high < low:
        raise DataValidationError("high below low")
    if not (low <= open_ <= high and low <= close <= high):
        raise DataValidationError("OHLC value outside candle range")
