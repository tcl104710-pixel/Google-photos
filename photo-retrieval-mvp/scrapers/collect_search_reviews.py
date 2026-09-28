"""scrapers/collect_search_reviews.py — Fetches, filters, and structures search-related reviews.

1. Fetches a large batch of reviews from Google Play + App Store.
2. Pre-filters them using search-related keywords to reduce LLM load.
3. Uses Groq to extract structured themes, problems, and intents.
4. Outputs the final filtered and structured dataset.
"""

import json
import logging
import os
import sys
import time
import asyncio
from pathlib import Path
from langdetect import detect, LangDetectException
from dotenv import load_dotenv
from google_play_scraper import Sort, reviews

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm.groq_client import GroqClient

load_dotenv()

# Configure logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/processed/scraper_progress.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

RAW_OUTPUT = Path("data/raw/large_raw_playstore.json")
FILTERED_OUTPUT = Path("data/processed/search_reviews.json")

KEYWORDS = [
    "search", "find", "finding", "found", "look", "looking", "scroll", "scrolling",
    "locate", "locating", "remember", "query", "sort", "filter", "tag", "face",
    "people", "where", "lost", "organize", "retrieve", "retrieving", "ask photos", "ai",
]

SYSTEM_PROMPT = """You are an expert UX Researcher analyzing app store reviews for Google Photos.
Determine if the review is related specifically to photo retrieval and photo search experience.

INCLUDE reviews about:
- Difficulty finding a specific photo
- Searching by context/event/activity/person/place/object/visual details
- Search accuracy or relevance problems
- Scrolling through many photos to find one
- Finding old photos or photos from events
- Finding similar/duplicate photos
- Irrelevant or missing search results
- Natural-language search issues
- Searching for people, places, objects, activities, text
- Ask Photos or AI-powered search
- Not knowing what keyword to search
- Poor organization/metadata affecting retrieval
- Expectations for better search
- Workarounds for finding photos
- Positive retrieval experiences

EXCLUDE reviews about:
- Storage/pricing complaints
- Backup/sync (unless it affects finding photos)
- Account/login problems
- General app crashes/performance
- Photo editing/sharing/printing

Return a JSON object. If relevant:
{"is_relevant": true, "theme": "...", "specific_problem": "...", "user_intent": "...", "workaround": null, "sentiment": "positive|negative|mixed"}

If NOT relevant:
{"is_relevant": false}"""


def fetch_large_batch_playstore(app_id: str, count: int) -> list[dict]:
    logger.info("Fetching up to %d Play Store reviews...", count)
    all_raw = []
    continuation_token = None
    batch_size = 200
    fetched = 0

    while fetched < count:
        try:
            result, continuation_token = reviews(
                app_id, lang="en", country="us", sort=Sort.NEWEST,
                count=batch_size, continuation_token=continuation_token,
            )
        except Exception as e:
            logger.error("Playstore fetch failed: %s", e)
            break
        if not result:
            break
        for r in result:
            all_raw.append({
                "source": "playstore",
                "id": str(r.get("reviewId")),
                "content": str(r.get("content", "")),
                "at": str(r.get("at", "")),
                "score": r.get("score", 0),
            })
        fetched += len(result)
        logger.info("Fetched %d Play Store reviews...", fetched)
        if not continuation_token:
            break
        time.sleep(1)
    return all_raw


def fetch_large_batch_appstore(app_id: str, count: int) -> list[dict]:
    import requests
    logger.info("Fetching up to %d App Store reviews...", count)
    all_raw = []
    pages_to_fetch = min(10, (count // 50) + (1 if count % 50 > 0 else 0))
    for page in range(1, pages_to_fetch + 1):
        url = f"https://itunes.apple.com/us/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            entries = resp.json().get("feed", {}).get("entry", [])
            if not entries:
                break
            for entry in entries:
                if "author" not in entry or "content" not in entry:
                    continue
                all_raw.append({
                    "source": "appstore",
                    "id": entry.get("id", {}).get("label", ""),
                    "content": entry.get("content", {}).get("label", ""),
                    "at": "Unknown",
                    "score": int(entry.get("im:rating", {}).get("label", "0")),
                })
                if len(all_raw) >= count:
                    break
            if len(all_raw) >= count:
                break
        except Exception as e:
            logger.error("Appstore fetch failed on page %d: %s", page, e)
            break
        time.sleep(1)
    logger.info("Fetched %d App Store reviews.", len(all_raw))
    return all_raw


def is_candidate(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    
    if not any(kw in t for kw in KEYWORDS):
        return False
        
    try:
        if detect(t) != "en":
            return False
    except LangDetectException:
        return False
        
    return True


async def process_reviews(raw_reviews: list[dict]) -> list[dict]:
    groq = GroqClient()
    candidates = [r for r in raw_reviews if is_candidate(r.get("content", ""))]
    logger.info("Keyword pre-filter: %d candidates out of %d raw reviews.", len(candidates), len(raw_reviews))

    structured = []
    errors = 0

    for i, review in enumerate(candidates):
        text = review.get("content", "")
        if i % 10 == 0:
            logger.info("LLM progress: %d / %d (relevant so far: %d, errors: %d)", i, len(candidates), len(structured), errors)

        try:
            result = await groq.generate_json(
                system_prompt=SYSTEM_PROMPT,
                user_message=text,
                temperature=0.0,
            )
            if result.get("is_relevant"):
                structured.append({
                    "source": review.get("source", "unknown"),
                    "review_text": text,
                    "review_date": str(review.get("at", "")),
                    "rating": review.get("score", 0),
                    "theme": result.get("theme"),
                    "specific_problem": result.get("specific_problem"),
                    "user_intent": result.get("user_intent"),
                    "workaround": result.get("workaround"),
                    "sentiment": result.get("sentiment"),
                })
        except Exception as e:
            errors += 1
            logger.warning("Review %d failed: %s", i, e)

        await asyncio.sleep(2)  # Rate limit buffer

    logger.info("LLM processing complete: %d relevant, %d errors out of %d candidates.", len(structured), errors, len(candidates))
    return structured


async def main():
    playstore_id = "com.google.android.apps.photos"
    appstore_id = "962194608"

    RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    FILTERED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    if RAW_OUTPUT.exists():
        logger.info("Loading cached raw reviews from %s", RAW_OUTPUT)
        with open(RAW_OUTPUT, "r", encoding="utf-8") as f:
            raw_reviews = json.load(f)
    else:
        raw_reviews = fetch_large_batch_playstore(playstore_id, 3000)
        raw_reviews.extend(fetch_large_batch_appstore(appstore_id, 500))
        with open(RAW_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(raw_reviews, f, indent=2, ensure_ascii=False, default=str)

    results = await process_reviews(raw_reviews)

    with open(FILTERED_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("Done! %d relevant reviews saved to %s", len(results), FILTERED_OUTPUT)


if __name__ == "__main__":
    asyncio.run(main())
