from types import SimpleNamespace

from app.anatomy_engine import detect_anatomies


def candle(o, h, l, c):
    return SimpleNamespace(open=o, high=h, low=l, close=c)


def test_lower_boundary_sweep_reclaim():
    candles = [candle(101, 105, 100, 104), candle(104, 104, 98, 99), candle(99, 106, 99, 105)]
    result = detect_anatomies(candles, "lower_boundary")
    assert result
    assert result[0].direction == "long"


def test_mid_range_is_not_detected():
    candles = [candle(100, 102, 99, 101)] * 3
    assert detect_anatomies(candles, "mid_range") == []
