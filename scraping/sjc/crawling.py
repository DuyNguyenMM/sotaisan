import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_FILE = Path("data/gold_prices.json")
URL = "https://sjc.com.vn/gia-vang-online"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GoldPriceScraper/1.0)"}
TIMEOUT = 10


@dataclass
class GoldEntry:
    name: str
    buy: str
    sell: str


def fetch_html(url: str) -> str:
    """Fetch raw HTML from the given URL."""
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.text


def parse_gold_table() -> list[GoldEntry]:
    entries = []
    raw_data = requests.post('https://sjc.com.vn/GoldPrice/Services/PriceService.ashx?BranchId=1')
    data = raw_data.json()
    for item in data['data']:
        if item['BranchName'] == 'Hồ Chí Minh':
            entries.append(GoldEntry(
                name=item['TypeName'],
                buy=item['BuyValue'],
                sell=item['SellValue']
            ))
    return entries


def save_to_json(entries: list[GoldEntry], path: Path) -> None:
    """Write parsed entries to a JSON file with metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "source": URL,
        "location": "Hồ Chí Minh",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "count": len(entries),
        "prices": [asdict(e) for e in entries],
    }

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )
    logger.info("Saved %d entries to %s", len(entries), path)


def get_gold_prices() -> list[GoldEntry]:
    """Main entry point: fetch, parse, and persist gold prices."""
    logger.info("Fetching gold prices from %s", URL)

    try:
        entries = parse_gold_table()

        if not entries:
            raise ValueError("Parsed table returned no entries — page structure may have changed.")

        save_to_json(entries, OUTPUT_FILE)
        return entries

    except requests.RequestException as e:
        logger.error("Network error: %s", e)
        raise
    except ValueError as e:
        logger.error("Parse error: %s", e)
        raise


if __name__ == "__main__":
    results = get_gold_prices()
    for entry in results:
        print(f"{entry.name:<30} buy={entry.buy}  sell={entry.sell}")