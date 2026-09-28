"""scrapers/playstore_scraper.py — Play Store review ingestion.

Fetches app reviews from the Google Play Store using the
google-play-scraper library.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google_play_scraper import Sort, reviews

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Output path
RAW_PLAYSTORE_PATH = Path("data/raw/raw_playstore.json")

# Required schema fields
_REQUIRED_FIELDS: list[str] = ["review_id", "rating", "text", "at"]

def _to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def _map_review(raw: dict) -> dict:
    return {
        "source": "playstore",
        "review_id": str(raw.get("reviewId") or ""),
        "author": raw.get("userName") or "",
        "rating": int(raw.get("score") or 0),
        "text": raw.get("content") or "",
        "thumbs_up": int(raw.get("thumbsUpCount") or 0),
        "at": _to_iso(raw.get("at")),
        "app_version": raw.get("appVersion") or "",
    }

def fetch_playstore_reviews(app_id: str, count: int) -> list[dict]:
    logger.info("Play Store scraper: starting — target %d reviews for %s.", count, app_id)

    all_reviews: list[dict] = []
    continuation_token = None
    batch_size = min(200, count)  # library max per call is 200
    fetched = 0
    batch_num = 0
    MAX_RETRIES = 3

    while fetched < count:
        batch_num += 1
        remaining = count - fetched
        this_batch = min(batch_size, remaining)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result, continuation_token = reviews(
                    app_id,
                    lang="en",
                    country="us",
                    sort=Sort.NEWEST,
                    count=this_batch,
                    continuation_token=continuation_token,
                )
                break
            except Exception as exc:
                if attempt == MAX_RETRIES:
                    raise RuntimeError(f"Play Store: failed after {MAX_RETRIES} attempts on batch {batch_num}.") from exc
                wait = 10 * attempt
                logger.warning("Play Store batch %d attempt %d failed (%s). Retrying in %ds.", batch_num, attempt, exc, wait)
                time.sleep(wait)

        if not result:
            logger.warning("Play Store: empty batch returned at batch %d — stopping.", batch_num)
            break

        for i, raw in enumerate(result):
            mapped = _map_review(raw)
            if all(mapped.get(f) for f in _REQUIRED_FIELDS):
                all_reviews.append(mapped)

        fetched += len(result)
        logger.debug("Play Store: batch %d fetched %d reviews (total so far: %d).", batch_num, len(result), fetched)

        if continuation_token is None:
            break

        if fetched < count:
            time.sleep(2)  # politeness delay

    logger.info("Play Store scraper: collected %d valid reviews.", len(all_reviews))
    return all_reviews

def run() -> list[dict]:
    app_id = os.getenv("PLAYSTORE_APP_ID", "com.google.android.apps.photos")
    count = int(os.getenv("PLAYSTORE_REVIEWS_COUNT", "100"))
    
    start = time.time()
    try:
        reviews_data = fetch_playstore_reviews(app_id=app_id, count=count)
    except Exception as exc:
        logger.error("Play Store scraper FAILED. Reason: %s", exc)
        return []

    RAW_PLAYSTORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_PLAYSTORE_PATH, "w", encoding="utf-8") as fh:
        json.dump(reviews_data, fh, indent=2, ensure_ascii=False, default=str)

    elapsed = time.time() - start
    logger.info("Play Store: %d reviews written to %s in %.1fs.", len(reviews_data), RAW_PLAYSTORE_PATH, elapsed)
    return reviews_data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run()
