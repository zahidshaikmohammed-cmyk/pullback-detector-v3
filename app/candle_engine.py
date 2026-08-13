from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from .market_data_ingestion import Candle


@dataclass(frozen=True)
class CandleWindow:
    instrument: str
    timeframe: str
    start: datetime
    end: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    complete: bool


class CandleEngine:
    """Builds deterministic fixed-time candles from validated candles."""

    def __init__(self, timeframe_minutes: int = 5) -> None:
        if timeframe_minutes <= 0:
            raise ValueError("timeframe_minutes must be positive")
        self.timeframe_minutes = timeframe_minutes

    def build(self, candles: Iterable[Candle]) -> list[CandleWindow]:
        ordered = sorted(candles, key=lambda item: (item.instrument, item.timestamp))
        windows: list[CandleWindow] = []
        buckets: dict[tuple[str, datetime], list[Candle]] = {}

        for candle in ordered:
            start = self._bucket_start(candle.timestamp)
            buckets.setdefault((candle.instrument, start), []).append(candle)

        duration = timedelta(minutes=self.timeframe_minutes)
        for (instrument, start), items in sorted(buckets.items()):
            items.sort(key=lambda item: item.timestamp)
            end = start + duration
            windows.append(
                CandleWindow(
                    instrument=instrument,
                    timeframe=f"{self.timeframe_minutes}m",
                    start=start,
                    end=end,
                    open=items[0].open,
                    high=max(item.high for item in items),
                    low=min(item.low for item in items),
                    close=items[-1].close,
                    volume=sum(item.volume for item in items),
                    complete=(items[-1].timestamp < end),
                )
            )
        return windows

    def _bucket_start(self, timestamp: datetime) -> datetime:
        minute = timestamp.minute - (timestamp.minute % self.timeframe_minutes)
        return timestamp.replace(minute=minute, second=0, microsecond=0)
