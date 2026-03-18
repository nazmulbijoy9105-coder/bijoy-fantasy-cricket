"""
scraper/utils.py  –  Shared scraper utilities
Governance: collect numeric stats only. No text commentary. No images.
"""

import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
DELAY = 2  # seconds between requests (be polite)


def fetch(url: str, retries: int = 3) -> BeautifulSoup | None:
    """Fetch a URL and return BeautifulSoup. Returns None on failure."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            time.sleep(DELAY)
            return BeautifulSoup(r.text, "html.parser")
        except requests.RequestException as e:
            print(f"[fetch] Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(DELAY * (attempt + 1))
    return None


def safe_int(val: str, default: int = 0) -> int:
    try:
        return int(str(val).strip().replace(",", "").split("/")[0])
    except (ValueError, AttributeError):
        return default


def safe_float(val: str, default: float = 0.0) -> float:
    try:
        cleaned = str(val).strip().replace(",", "")
        return float(cleaned) if cleaned not in ("-", "", "N/A", "DNB") else default
    except (ValueError, AttributeError):
        return default


def parse_overs(overs_str: str) -> float:
    """Convert '18.4' overs string to decimal overs."""
    try:
        parts = str(overs_str).strip().split(".")
        return int(parts[0]) + (int(parts[1]) / 6 if len(parts) > 1 else 0)
    except Exception:
        return 0.0
