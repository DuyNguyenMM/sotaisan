# python
import json
import requests
from pathlib import Path

import pytest

from scraping.doji import crawling

SAMPLE_HTML = """
<html>
  <body>
    <h2>Giá vàng trong nước</h2>
    <table>
      <tr><th>Name</th><th>Buy</th><th>Sell</th></tr>
      <tr><td>SJC 1L</td><td>60.000</td><td>60.500</td></tr>
      <tr><td>SJC 2L</td><td>61.000</td><td>61.500</td></tr>
    </table>
  </body>
</html>
"""


def test_parse_gold_table_parses_entries():
    entries = crawling.parse_gold_table(SAMPLE_HTML)
    assert len(entries) == 2
    assert entries[0].name == "SJC 1L"
    assert entries[0].buy == "60.000"
    assert entries[0].sell == "60.500"


def test_parse_gold_table_raises_if_header_missing():
    html = "<html><body><h2>Other header</h2><table></table></body></html>"
    with pytest.raises(ValueError):
        crawling.parse_gold_table(html)


def test_save_to_json_writes_file(tmp_path: Path):
    entries = [
        crawling.GoldEntry(name="A", buy="1", sell="2"),
        crawling.GoldEntry(name="B", buy="3", sell="4"),
    ]
    out = tmp_path / "gold.json"
    crawling.save_to_json(entries, out)

    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["source"] == crawling.URL
    assert data["location"] == "Hồ Chí Minh"
    assert data["count"] == 2
    assert isinstance(data["scraped_at"], str)
    assert data["prices"][0]["name"] == "A"
    assert data["prices"][1]["buy"] == "3"


def test_get_gold_prices_success_and_persists(tmp_path: Path, monkeypatch):
    # stub fetch_html to return sample HTML
    monkeypatch.setattr(crawling, "fetch_html", lambda url=crawling.URL: SAMPLE_HTML)
    out = tmp_path / "out.json"
    monkeypatch.setattr(crawling, "OUTPUT_FILE", out)

    results = crawling.get_gold_prices()
    assert len(results) == 2
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["count"] == 2


def test_get_gold_prices_retries_on_failure_then_succeeds(tmp_path: Path, monkeypatch):
    # first call raises, second returns HTML
    state = {"calls": 0}

    def flaky_fetch(url=crawling.URL):
        if state["calls"] == 0:
            state["calls"] += 1
            raise requests.RequestException("simulated network error")
        return SAMPLE_HTML

    monkeypatch.setattr(crawling, "fetch_html", flaky_fetch)
    out = tmp_path / "retry.json"
    monkeypatch.setattr(crawling, "OUTPUT_FILE", out)

    results = crawling.get_gold_prices()
    assert len(results) == 2
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["count"] == 2