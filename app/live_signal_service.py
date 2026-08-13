from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from zoneinfo import ZoneInfo

from .dhan_live_adapter import DhanLiveDataAdapter, DhanLiveDataError
from .location_engine import classify_location
from .pipeline_orchestrator import run_pipeline


IST = ZoneInfo("Asia/Kolkata")
POLL_SECONDS = float(os.getenv("V3_POLL_SECONDS", "5"))
LOOKBACK = int(os.getenv("V3_LOOKBACK", "60"))
REQUIRE_TODAY = os.getenv("V3_REQUIRE_TODAY", "true").lower() == "true"

ADAPTER = DhanLiveDataAdapter()

STATE: dict[str, Any] = {
    "status": "starting",
    "updated_at": None,
    "source": "DHAN",
    "instrument": os.getenv("V3_DHAN_SYMBOL", "NIFTY"),
    "security_id": os.getenv("V3_DHAN_SECURITY_ID", "13"),
    "interval": os.getenv("V3_DHAN_INTERVAL", "1"),
    "signal": None,
    "entry": None,
    "regime": None,
    "location": None,
    "error": None,
    "candles": 0,
    "latest_candle": None,
}
LOCK = threading.Lock()


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
    candles = ADAPTER.fetch_today() if REQUIRE_TODAY else ADAPTER.fetch_candles()
    if not candles:
        raise DhanLiveDataError("Dhan returned no current-session candles")

    latest_instrument = candles[-1].instrument
    series = [c for c in candles if c.instrument == latest_instrument][-LOOKBACK:]
    if len(series) < 12:
        raise DhanLiveDataError(f"insufficient current-session candles: {len(series)} < 12")

    latest = series[-1]
    now_ist = datetime.now(IST)
    age_seconds = (now_ist - latest.timestamp.astimezone(IST)).total_seconds()
    max_age = max(120.0, float(os.getenv("V3_MAX_CANDLE_AGE_SECONDS", "120")))
    if age_seconds > max_age:
        raise DhanLiveDataError(f"stale Dhan candle: {int(age_seconds)}s old")

    range_low = min(c.low for c in series)
    range_high = max(c.high for c in series)
    location_result = classify_location(latest.close, range_low, range_high)
    result = run_pipeline(series, location_result.location)

    with LOCK:
        STATE.update(
            {
                "status": "live",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "signal": _serialize(result.signal),
                "entry": _serialize(result.entry),
                "regime": _serialize(result.regime),
                "location": _serialize(location_result),
                "error": None,
                "candles": len(series),
                "latest_candle": _serialize(latest),
            }
        )


def worker() -> None:
    while True:
        try:
            evaluate()
        except Exception as exc:
            with LOCK:
                STATE.update(
                    {
                        "status": "waiting",
                        "error": str(exc),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
        time.sleep(POLL_SECONDS)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path not in {"/", "/health", "/signal", "/state"}:
            self.send_response(404)
            self.end_headers()
            return
        with LOCK:
            body = json.dumps(STATE, default=str).encode()
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
