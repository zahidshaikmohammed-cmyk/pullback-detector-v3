from datetime import datetime, timedelta, timezone

from app.candle_engine import CandleEngine
from app.market_data_ingestion import Candle, MarketDataIngestion
from app.pipeline_orchestrator import run_pipeline


def test_ingestion_to_candle_engine():
    base = datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc)
    raw = [
        Candle("NIFTY", base + timedelta(minutes=i), 100 + i, 102 + i, 99 + i, 101 + i, 1000)
        for i in range(5)
    ]
    accepted = MarketDataIngestion().ingest(raw)
    windows = CandleEngine(5).build(accepted)
    assert len(windows) == 1
    assert windows[0].open == 100
    assert windows[0].close == 105
    assert windows[0].volume == 5000


def test_pipeline_returns_structured_result():
    candles = [
        Candle("NIFTY", datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(minutes=i),
               100 + i, 101 + i, 99 + i, 100.5 + i, 1000)
        for i in range(30)
    ]
    result = run_pipeline(candles, "mid_range")
    assert result.regime is not None
    assert isinstance(result.anatomies, list)
    assert isinstance(result.confirmations, list)
