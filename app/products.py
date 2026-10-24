import json
from datetime import date
from pathlib import Path

_FILE = Path(__file__).with_name("products.json")

def all_products() -> list[dict]:
    return json.loads(_FILE.read_text(encoding="utf-8"))

def product_of_the_day(day: date | None = None) -> dict:
    """Rotates through the catalogue so every day features a different product."""
    day = day or date.today()
    items = all_products()
    return items[day.toordinal() % len(items)]
