from datetime import datetime, timezone

from app.models.schemas import Candle
from app.data.validator import validate_ohlc, DataValidationError


def test_candle_schema_is_constructible():
    candle = Candle("NIFTY", "1m", datetime.now(timezone.utc), datetime.now(timezone.utc), 1, 2, 0, 1.5, 100, True)
    assert candle.close == 1.5


def test_validator_accepts_valid_ohlc():
    validate_ohlc(101, 105, 99, 103)


def test_validator_rejects_invalid_ohlc():
    try:
        validate_ohlc(101, 100, 99, 100)
    except DataValidationError:
        return
    raise AssertionError("invalid OHLC was accepted")
