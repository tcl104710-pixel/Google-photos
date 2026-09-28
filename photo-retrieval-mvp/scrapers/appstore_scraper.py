"""scrapers/appstore_scraper.py — App Store review ingestion.

Fetches app reviews from the Apple App Store using the iTunes RSS feed.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

RAW_APPSTORE_PATH = Path("data/raw/raw_appstore.json")

def fetch_appstore_reviews(app_id: str, count: int) -> list[dict]:
    logger.info("App Store scraper: starting — target %d reviews for app_id %s.", count, app_id)

    all_reviews: list[dict] = []
    
    # iTunes RSS feed limits to 10 pages of 50 reviews = 500 reviews max
    pages_to_fetch = min(10, (count // 50) + (1 if count % 50 > 0 else 0))
    
    for page in range(1, pages_to_fetch + 1):
        url = f"https://itunes.apple.com/us/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
        
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            entries = data.get("feed", {}).get("entry", [])
            if not entries:
                break
                
            # The first entry in the RSS feed is often the app metadata, not a review
            # A review entry usually has an author with a uri, and content
            for entry in entries:
                if "author" not in entry or "content" not in entry:
                    continue
                    
                review_id = entry.get("id", {}).get("label", "")
                author = entry.get("author", {}).get("name", {}).get("label", "")
                rating = int(entry.get("im:rating", {}).get("label", "0"))
                text = entry.get("content", {}).get("label", "")
                version = entry.get("im:version", {}).get("label", "")
                
                all_reviews.append({
                    "source": "appstore",
                    "review_id": str(review_id),
                    "author": author,
                    "rating": rating,
                    "text": text,
                    "thumbs_up": 0,
                    "at": datetime.now(timezone.utc).isoformat(), # RSS feed doesn't provide date, mock with current
                    "app_version": version,
                })
                
                if len(all_reviews) >= count:
                    break
                    
            if len(all_reviews) >= count:
                break
                
        except Exception as e:
            logger.error("Failed to fetch App Store page %d: %s", page, e)
            break
            
        time.sleep(1) # Politeness

    logger.info("App Store scraper: collected %d valid reviews.", len(all_reviews))
    return all_reviews

def run() -> list[dict]:
    app_id = os.getenv("APPSTORE_APP_ID", "962194608")
    count = int(os.getenv("APPSTORE_REVIEWS_COUNT", "100"))
    
    start = time.time()
    try:
        reviews_data = fetch_appstore_reviews(app_id=app_id, count=count)
    except Exception as exc:
        logger.error("App Store scraper FAILED. Reason: %s", exc)
        return []

    RAW_APPSTORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_APPSTORE_PATH, "w", encoding="utf-8") as fh:
        json.dump(reviews_data, fh, indent=2, ensure_ascii=False, default=str)

    elapsed = time.time() - start
    logger.info("App Store: %d reviews written to %s in %.1fs.", len(reviews_data), RAW_APPSTORE_PATH, elapsed)
    return reviews_data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run()
