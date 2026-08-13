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
MAX_AGE = max(120.0, float(os.getenv("V3_MAX_CANDLE_AGE_SECONDS", "120")))
ADAPTER = DhanLiveDataAdapter()
STARTED_AT = datetime.now(timezone.utc).isoformat()

STATE: dict[str, Any] = {
    "status": "starting",
    "started_at": STARTED_AT,
    "updated_at": None,
    "source": "DHAN",
    "instrument": os.getenv("V3_DHAN_SYMBOL", "NIFTY"),
    "security_id": os.getenv("V3_DHAN_SECURITY_ID", "13"),
    "interval": os.getenv("V3_DHAN_INTERVAL", "1"),
    "dhan_auth": "configured",
    "data_received": False,
    "last_candle": None,
    "candle_age_seconds": None,
    "pipeline_status": "not_evaluated",
    "signal": None,
    "entry": None,
    "regime": None,
    "location": None,
    "error": None,
    "candles": 0,
    "evaluation_count": 0,
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


def _safe_error(exc: Exception) -> str:
    text = str(exc)
    for secret in (getattr(ADAPTER, "client_id", ""), getattr(ADAPTER, "access_token", "")):
        if secret:
            text = text.replace(secret, "***")
    return text


def evaluate() -> None:
    candles = ADAPTER.fetch_today() if REQUIRE_TODAY else ADAPTER.fetch_candles()
    if not candles:
        raise DhanLiveDataError("Dhan returned no current-session candles")

    latest_instrument = candles[-1].instrument
    series = [c for c in candles if c.instrument == latest_instrument][-LOOKBACK:]
    if len(series) < 12:
        raise DhanLiveDataError(f"insufficient current-session candles: {len(series)} < 12")

    latest = series[-1]
    age_seconds = (datetime.now(IST) - latest.timestamp.astimezone(IST)).total_seconds()
    if age_seconds > MAX_AGE:
        raise DhanLiveDataError(f"stale Dhan candle: {int(age_seconds)}s old")

    range_low = min(c.low for c in series)
    range_high = max(c.high for c in series)
    location_result = classify_location(latest.close, range_low, range_high)
    result = run_pipeline(series, location_result.location)

    with LOCK:
        STATE.update({
            "status": "live",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "data_received": True,
            "last_candle": latest.timestamp.isoformat(),
            "candle_age_seconds": round(max(0.0, age_seconds), 2),
            "pipeline_status": "evaluated",
            "signal": _serialize(result.signal),
            "entry": _serialize(result.entry),
            "regime": _serialize(result.regime),
            "location": _serialize(location_result),
            "error": None,
            "candles": len(series),
            "evaluation_count": STATE["evaluation_count"] + 1,
        })


def worker() -> None:
    while True:
        try:
            evaluate()
        except Exception as exc:
            with LOCK:
                STATE.update({
                    "status": "waiting",
                    "data_received": False,
                    "pipeline_status": "blocked",
                    "error": _safe_error(exc),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
        time.sleep(POLL_SECONDS)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/probe":
            with LOCK:
                payload = {
                    "service": "pullback-detector-v3",
                    "reachable": True,
                    "status": STATE["status"],
                    "started_at": STATE["started_at"],
                    "updated_at": STATE["updated_at"],
                    "dhan_auth": STATE["dhan_auth"],
                    "data_received": STATE["data_received"],
                    "last_candle": STATE["last_candle"],
                    "candle_age_seconds": STATE["candle_age_seconds"],
                    "pipeline_status": STATE["pipeline_status"],
                    "evaluation_count": STATE["evaluation_count"],
                    "error": STATE["error"],
                }
            body = json.dumps(payload, default=str).encode()
        elif self.path in {"/", "/health", "/signal", "/state"}:
            with LOCK:
                body = json.dumps(STATE, default=str).encode()
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
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
