from datetime import datetime

import pytest

from app.dhan_live_adapter import DhanLiveDataAdapter, DhanLiveDataError


class FakeResponse:
    status_code = 200

    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, headers, json, timeout):
        self.calls.append((url, headers, json, timeout))
        return self.response


def adapter(body):
    session = FakeSession(FakeResponse(body))
    instance = DhanLiveDataAdapter(
        client_id="client",
        access_token="token",
        security_id="13",
        exchange_segment="IDX_I",
        instrument="INDEX",
        interval="1",
        session=session,
    )
    return instance, session


def test_parses_dhan_array_response():
    instance, session = adapter(
        {
            "data": {
                "open": [100, 101],
                "high": [102, 103],
                "low": [99, 100],
                "close": [101, 102],
                "volume": [1000, 1100],
                "timestamp": [1767222900, 1767222960],
            }
        }
    )

    candles = instance.fetch_candles(1)

    assert len(candles) == 2
    assert candles[0].instrument == "NIFTY"
    assert candles[-1].close == 102
    assert session.calls[0][2]["securityId"] == "13"
    assert session.calls[0][1]["client-id"] == "client"
    assert "token" in session.calls[0][1]["access-token"]


def test_rejects_empty_response():
    instance, _ = adapter({"data": {"open": [], "high": [], "low": [], "close": [], "volume": [], "timestamp": []}})
    with pytest.raises(DhanLiveDataError, match="no candles"):
        instance.fetch_candles(1)


def test_rejects_invalid_interval():
    with pytest.raises(DhanLiveDataError, match="interval"):
        DhanLiveDataAdapter(
            client_id="client",
            access_token="token",
            interval="7",
        )
