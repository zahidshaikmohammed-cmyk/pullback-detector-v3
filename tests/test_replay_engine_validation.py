from datetime import datetime, timedelta, timezone

from app.market_data_ingestion import Candle
from app.pipeline_orchestrator import run_pipeline


def make_case(symbol, closes):
    base = datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc)
    return [
        Candle(symbol, base + timedelta(minutes=i), close - 0.5, close + 1, close - 1, close, 1000 + i)
        for i, close in enumerate(closes)
    ]


def test_replay_is_deterministic():
    candles = make_case("NIFTY", [100, 99, 98, 99, 100, 101, 100, 99, 98, 99] * 3)
    first = run_pipeline(candles, "lower_boundary")
    second = run_pipeline(candles, "lower_boundary")

    assert first == second


def test_replay_preserves_result_shape():
    candles = make_case("NIFTY", list(range(100, 130)))
    result = run_pipeline(candles, "mid_range")

    assert result.regime is not None
    assert isinstance(result.anatomies, list)
    assert isinstance(result.confirmations, list)
    assert isinstance(result.signal, (dict, type(None)))
    assert isinstance(result.entry, (dict, type(None)))


def test_replay_case_isolated_between_runs():
    case_a = make_case("NIFTY", [100, 99, 98, 99, 100] * 6)
    case_b = make_case("NIFTY", [100, 101, 102, 101, 100] * 6)

    result_a = run_pipeline(case_a, "lower_boundary")
    result_b = run_pipeline(case_b, "upper_boundary")
    result_a_again = run_pipeline(case_a, "lower_boundary")

    assert result_a == result_a_again
    assert result_a is not result_b
