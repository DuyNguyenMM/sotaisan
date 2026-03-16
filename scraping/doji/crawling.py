import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup

from utils.timer import get_scraped_time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_FILE = Path("data/gold_prices.json")
URL = "https://giavang.doji.vn/"
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


def parse_gold_table(html: str) -> list[GoldEntry]:
    """Parse the domestic gold price table from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    header = soup.find(
        lambda tag: tag.name in ["h2", "h3", "div"]
        and "Giá vàng trong nước" in tag.get_text()
    )
    if not header:
        raise ValueError("Could not find 'Giá vàng trong nước' header.")

    table = header.find_next("table")
    if not table:
        raise ValueError("Could not find the gold price table.")

    entries: list[GoldEntry] = []

    for row in table.find_all("tr")[1:]:  # skip header row
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        name = cols[0].get_text(strip=True)
        buy  = cols[1].get_text(strip=True) if len(cols) > 1 else "N/A"
        sell = cols[2].get_text(strip=True) if len(cols) > 2 else "N/A"

        if not name:
            continue

        entries.append(GoldEntry(name=" ".join(name.split()), buy=buy, sell=sell))

    return entries


def save_to_json(entries: list[GoldEntry], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": URL,
        "location": "Hồ Chí Minh",
        "scraped_at": get_scraped_time(),
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
    retry = 3
    attempt = 0
    try:
        html = fetch_html(URL)
        entries = parse_gold_table(html)

        if not entries:
            raise ValueError("Parsed table returned no entries — page structure may have changed.")

        save_to_json(entries, OUTPUT_FILE)
        return entries

    except Exception as e:
        logger.error("Error: %s", e)
        if attempt < retry:
            logger.info("Retrying... (%d/%d)", attempt + 1, retry)
            return get_gold_prices()
        else:
            logger.error("Failed after %d attempts.", retry)
            raise


if __name__ == "__main__":
    results = get_gold_prices()
    for entry in results:
        print(f"{entry.name:<30} buy={entry.buy}  sell={entry.sell}")