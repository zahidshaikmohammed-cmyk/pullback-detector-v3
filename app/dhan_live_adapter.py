from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import requests

from .market_data_ingestion import Candle


DHAN_INTRADAY_URL = "https://api.dhan.co/v2/charts/intraday"
IST = ZoneInfo("Asia/Kolkata")


class DhanLiveDataError(RuntimeError):
    """Raised when Dhan live candle acquisition fails or returns invalid data."""


class DhanLiveDataAdapter:
    """Read fresh intraday candles directly from DhanHQ using server-side credentials.

    Credentials are read only from environment variables and are never included in
    returned objects or exception messages.
    """

    def __init__(
        self,
        client_id: str | None = None,
        access_token: str | None = None,
        security_id: str | None = None,
        exchange_segment: str | None = None,
        instrument: str | None = None,
        interval: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.client_id = client_id or os.getenv("DHAN_CLIENT_ID") or os.getenv("DHAN_CLIENTID")
        self.access_token = access_token or os.getenv("DHAN_ACCESS_TOKEN") or os.getenv("DHAN_ACCESS_TOKEN_V2")
        self.security_id = security_id or os.getenv("V3_DHAN_SECURITY_ID", "13")
        self.exchange_segment = exchange_segment or os.getenv("V3_DHAN_EXCHANGE_SEGMENT", "IDX_I")
        self.instrument = instrument or os.getenv("V3_DHAN_INSTRUMENT", "INDEX")
        self.interval = interval or os.getenv("V3_DHAN_INTERVAL", "1")
        self.session = session or requests.Session()

        if not self.client_id or not self.access_token:
            raise DhanLiveDataError("DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN are required")
        if self.interval not in {"1", "5", "15", "25", "60"}:
            raise DhanLiveDataError("V3_DHAN_INTERVAL must be one of 1, 5, 15, 25, 60")

    def fetch_candles(self, lookback_days: int = 5) -> list[Candle]:
        if lookback_days < 1 or lookback_days > 90:
            raise DhanLiveDataError("lookback_days must be between 1 and 90")

        today = datetime.now(IST).date()
        from_date = today - timedelta(days=lookback_days)
        to_date = today + timedelta(days=1)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "access-token": self.access_token,
            "client-id": self.client_id,
        }
        payload = {
            "securityId": str(self.security_id),
            "exchangeSegment": self.exchange_segment,
            "instrument": self.instrument,
            "interval": self.interval,
            "oi": False,
            "fromDate": from_date.strftime("%Y-%m-%d %H:%M:%S"),
            "toDate": to_date.strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            response = self.session.post(DHAN_INTRADAY_URL, headers=headers, json=payload, timeout=10)
        except requests.RequestException as exc:
            raise DhanLiveDataError("Dhan market-data request failed") from exc

        if response.status_code >= 400:
            raise DhanLiveDataError(f"Dhan market-data request returned HTTP {response.status_code}")

        try:
            body = response.json()
        except ValueError as exc:
            raise DhanLiveDataError("Dhan returned non-JSON market data") from exc

        return self._parse_candles(body)

    def fetch_today(self) -> list[Candle]:
        today = datetime.now(IST).date()
        candles = self.fetch_candles(lookback_days=1)
        return [candle for candle in candles if candle.timestamp.astimezone(IST).date() == today]

    def _parse_candles(self, body: Any) -> list[Candle]:
        data = body.get("data", body) if isinstance(body, dict) else None
        if not isinstance(data, dict):
            raise DhanLiveDataError("Dhan response does not contain candle data")

        opens = data.get("open", [])
        highs = data.get("high", [])
        lows = data.get("low", [])
        closes = data.get("close", [])
        volumes = data.get("volume", [0] * len(closes))
        timestamps = data.get("timestamp", [])

        arrays = (opens, highs, lows, closes, volumes, timestamps)
        if not all(isinstance(values, list) for values in arrays):
            raise DhanLiveDataError("Dhan candle arrays are malformed")
        if not timestamps or not closes:
            raise DhanLiveDataError("Dhan returned no candles")

        size = min(map(len, arrays))
        candles: list[Candle] = []
        for index in range(size):
            try:
                timestamp = self._timestamp(timestamps[index])
                candle = Candle(
                    instrument=self._instrument_name(),
                    timestamp=timestamp,
                    open=float(opens[index]),
                    high=float(highs[index]),
                    low=float(lows[index]),
                    close=float(closes[index]),
                    volume=float(volumes[index]),
                )
            except (TypeError, ValueError, OverflowError):
                continue
            candles.append(candle)

        candles.sort(key=lambda candle: candle.timestamp)
        if not candles:
            raise DhanLiveDataError("Dhan returned no valid candles")
        return candles

    def _timestamp(self, value: Any) -> datetime:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc).astimezone(IST)
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=IST)
        return parsed.astimezone(IST)

    def _instrument_name(self) -> str:
        symbol = os.getenv("V3_DHAN_SYMBOL", "NIFTY")
        return symbol.strip() or "NIFTY"
