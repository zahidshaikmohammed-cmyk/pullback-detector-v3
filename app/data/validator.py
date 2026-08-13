"""Fail-closed market data validation boundary."""

class DataValidationError(ValueError):
    """Raised when market data cannot be trusted."""

def validate_ohlc(open_: float, high: float, low: float, close: float) -> None:
    if low > high:
        raise DataValidationError("low cannot exceed high")
    if not (low <= open_ <= high and low <= close <= high):
        raise DataValidationError("OHLC value outside candle range")
