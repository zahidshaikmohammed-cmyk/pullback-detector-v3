from datetime import datetime, timedelta, timezone

from app.market_data_ingestion import Candle
from app.pipeline_orchestrator import run_pipeline


def test_e2e_market_data_to_pipeline_output():
    base = datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc)
    candles = []
    prices = [100, 99, 98, 99, 100, 101, 100, 99, 98, 97, 98, 99, 100, 101, 102,
              101, 100, 99, 98, 99, 100, 101, 102, 103, 102, 101, 100, 99, 100, 101]
    for i, close in enumerate(prices):
        candles.append(
            Candle(
                "NIFTY",
                base + timedelta(minutes=i),
                close - 0.5,
                close + 1,
                close - 1,
                close,
                1000 + i,
            )
        )

    result = run_pipeline(candles, "lower_boundary")

    assert result.regime is not None
    assert isinstance(result.anatomies, list)
    assert isinstance(result.confirmations, list)
    if result.signal is not None:
        assert result.entry is not None


def test_e2e_rejects_insufficient_market_data_without_crashing():
    base = datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc)
    candles = [
        Candle("NIFTY", base + timedelta(minutes=i), 100, 101, 99, 100, 1000)
        for i in range(3)
    ]
    result = run_pipeline(candles, "mid_range")
    assert result.regime.regime == "unknown"
    assert result.signal is None
    assert result.entry is None
