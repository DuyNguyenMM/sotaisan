import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup

from utils.timer import get_scraped_time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_FILE = Path("data/doji/gold_prices.json")
URL = "https://giavang.doji.vn/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GoldPriceScraper/1.0)"}
TIMEOUT = 10
MAX_RETRIES = 3


@dataclass
class GoldEntry:
    name: str
    buy: int
    sell: int


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.text


def parse_gold_table(html: str) -> list[GoldEntry]:
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
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        name = cols[0].get_text(strip=True)
        buy  = cols[1].get_text(strip=True) if len(cols) > 1 else "N/A"
        sell = cols[2].get_text(strip=True) if len(cols) > 2 else "N/A"
        if not name:
            continue

        buy = int(buy.replace(",", ""))*1000 if buy != "N/A" else 0
        sell = int(sell.replace(",", ""))*1000 if sell != "N/A" else 0
        entries.append(GoldEntry(name=" ".join(name.split()), buy=buy, sell=sell))

    return entries


def save_to_json(brand: str, entries: list[GoldEntry], path: Path) -> None:
    """
    Upsert brand data into the JSON file.
    - Creates the file if it doesn't exist
    - Replaces only the data for this brand, preserving other brands
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        # Kiểm tra xem payload có tạo được không
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
        print("Ghi file thành công!")
        logger.info("Upserted %d entries for brand '%s' into %s", len(entries), brand, path)
    except Exception as e:
        print(f"Lỗi rồi đại vương ơi: {e}")


def get_gold_prices(brand: str = "doji") -> list[GoldEntry]:
    """Fetch, parse, and persist gold prices. Retries up to MAX_RETRIES times."""
    logger.info("Fetching gold prices from %s", URL)

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            html = fetch_html(URL)
            entries = parse_gold_table(html)

            if not entries:
                raise ValueError("Parsed table returned no entries — page structure may have changed.")

            save_to_json(brand, entries, OUTPUT_FILE)
            return entries

        except Exception as e:
            last_error = e
            logger.warning("Attempt %d/%d failed: %s", attempt, MAX_RETRIES, e)

    logger.error("All %d attempts failed.", MAX_RETRIES)
    raise RuntimeError(f"Scraping failed after {MAX_RETRIES} attempts") from last_error


if __name__ == "__main__":
    results = get_gold_prices("doji")
    for entry in results:
        print(f"{entry.name:<30} buy={entry.buy}  sell={entry.sell}")