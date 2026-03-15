BRAND_NAME = ['doji', 'sjc', 'btmc', 'btmh', 'mihong']
from .sjc import crawling as sjc_crawling
from .doji import crawling as doji_crawling

def trigger_scraping(brand):
    """Trigger the scraping process for a specific brand."""
    if brand not in BRAND_NAME:
        raise ValueError(f"Invalid brand '{brand}'. Valid options are: {', '.join(BRAND_NAME)}.")
    # Here you would implement the actual scraping logic, e.g. by calling a scraper function or script.
    if brand == 'doji':
        doji_crawling.get_gold_prices()
    elif brand == 'sjc':
        sjc_crawling.get_gold_prices()
    print(f"Completed scraping data for brand '{brand}'.")