import json
from pathlib import Path

BRAND_NAME = ['doji', 'sjc', 'btmc', 'btmh', 'mihong']
def get_data_by_brand(brand: str) -> list[dict]:
    """Extract price data for a specific brand."""
    if brand not in BRAND_NAME:
        raise ValueError(f"Invalid brand '{brand}'. Valid options are: {', '.join(BRAND_NAME)}.")
    data_file = Path(f"data/{brand}/gold_prices.json")
    return json.loads(data_file.read_text(encoding="utf-8"))