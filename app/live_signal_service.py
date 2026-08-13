from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import requests

from .location_engine import classify_location
from .market_data_ingestion import Candle, MarketDataIngestion
from .pipeline_orchestrator import run_pipeline


POLL_SECONDS = float(os.getenv("V3_POLL_SECONDS", "5"))
LOOKBACK = int(os.getenv("V3_LOOKBACK", "60"))
LIVE_MARKET_URL = os.getenv("V3_LIVE_MARKET_URL", "https://psycho-market-bridge.onrender.com/market-live.json")

STATE: dict[str, Any] = {
    "status": "starting",
    "updated_at": None,
    "source": LIVE_MARKET_URL,
    "signal": None,
    "entry": None,
    "regime": None,
    "location": None,
    "error": None,
    "candles": 0,
}
LOCK = threading.Lock()


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("candles", "data", "market_data", "bars"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    return []


def _to_candles(payload: Any) -> list[Candle]:
    rows = _extract_rows(payload)
    candles: list[Candle] = []
    for row in rows:
        try:
            instrument = row.get("instrument") or row.get("symbol") or row.get("security") or "NIFTY"
            timestamp = row.get("timestamp") or row.get("time") or row.get("datetime")
            candles.append(
                Candle(
                    str(instrument),
                    _parse_timestamp(timestamp),
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    float(row.get("volume", 0)),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    candles.sort(key=lambda c: (c.instrument, c.timestamp))
    return candles


def _serialize(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__"):
        return {k: _serialize(v) for k, v in asdict(value).items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


def evaluate() -> None:
    response = requests.get(LIVE_MARKET_URL, timeout=10)
    response.raise_for_status()
    candles = _to_candles(response.json())
    if not candles:
        raise RuntimeError("live feed returned no valid candles")

    latest_instrument = candles[-1].instrument
    series = [c for c in candles if c.instrument == latest_instrument][-LOOKBACK:]
    if len(series) < 12:
        raise RuntimeError(f"insufficient candles: {len(series)} < 12")

    range_low = min(c.low for c in series)
    range_high = max(c.high for c in series)
    location_result = classify_location(series[-1].close, range_low, range_high)
    result = run_pipeline(series, location_result.location)

    with LOCK:
        STATE.update(
            {
                "status": "live",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "signal": _serialize(result.signal),
                "entry": _serialize(result.entry),
                "regime": _serialize(result.regime),
                "location": _serialize(location_result),
                "error": None,
                "candles": len(series),
            }
        )


def worker() -> None:
    while True:
        try:
            evaluate()
        except Exception as exc:
            with LOCK:
                STATE.update({"status": "error", "error": str(exc), "updated_at": datetime.utcnow().isoformat() + "Z"})
        time.sleep(POLL_SECONDS)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path not in {"/", "/health", "/signal", "/state"}:
            self.send_response(404)
            self.end_headers()
            return
        with LOCK:
            body = json.dumps(STATE).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    threading.Thread(target=worker, daemon=True).start()
    port = int(os.getenv("PORT", "10000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
