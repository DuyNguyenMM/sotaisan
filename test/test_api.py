# python
import json
from fastapi.testclient import TestClient
import main
import pytest

SAMPLE_DATA = {
    "prices": [
        {"name": "SJC 1L", "buy": "60.000", "sell": "60.500"},
        {"name": "SJC 2L", "buy": "61.000", "sell": "61.500"},
    ],
    "count": 2,
}

def test_get_gold_price_success_calls_trigger_and_returns_data(monkeypatch):
    called = {"args": None}
    def fake_trigger(brand):
        called["args"] = brand

    def fake_get_data_by_brand(brand):
        return SAMPLE_DATA

    monkeypatch.setattr(main, "trigger_scraping", fake_trigger)
    monkeypatch.setattr(main, "get_data_by_brand", fake_get_data_by_brand)

    client = TestClient(main.app)
    resp = client.get("/api/v1/gold/price", params={"brand": "doji"})
    assert resp.status_code == 200
    assert resp.json() == SAMPLE_DATA
    assert called["args"] == "doji"

def test_get_gold_price_not_found_returns_404(monkeypatch):
    def fake_trigger(brand):
        pass

    def fake_get_data_by_brand(brand):
        return None  # simulates missing brand

    monkeypatch.setattr(main, "trigger_scraping", fake_trigger)
    monkeypatch.setattr(main, "get_data_by_brand", fake_get_data_by_brand)

    client = TestClient(main.app)
    resp = client.get("/api/v1/gold/price", params={"brand": "unknown"})
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body
    assert "not found" in body["detail"].lower()