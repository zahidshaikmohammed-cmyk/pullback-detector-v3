from types import SimpleNamespace

from app.regime_engine import classify_regime


def candle(c):
    return SimpleNamespace(open=c, high=c + 1, low=c - 1, close=c)


def test_short_input_is_unknown():
    assert classify_regime([candle(100)] * 3).regime == "unknown"


def test_low_efficiency_series_can_be_sideways():
    prices = [100, 101, 99, 100, 101, 99, 100, 101, 99, 100, 101, 100]
    result = classify_regime([candle(p) for p in prices])
    assert result.regime in {"sideways", "transitional"}
