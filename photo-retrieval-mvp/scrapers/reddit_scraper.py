"""scrapers/reddit_scraper.py — Reddit discussion ingestion using Apify.

Fetches Reddit posts and discussions using the Apify API (automation-lab/reddit-scraper).
Includes keyword filtering, theme detection, and sentiment analysis to output
a processed dataset specifically for photo retrieval research.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from langdetect import detect, LangDetectException

from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

RAW_OUTPUT = Path("data/raw/raw_reddit.json")
FILTERED_OUTPUT = Path("data/processed/reddit_search_posts.json")

# Keywords that indicate a post is about photo retrieval
INCLUDE_KEYWORDS = [
    "search", "find", "finding", "found", "can't find", "cannot find",
    "look for", "looking for", "scroll", "scrolling",
    "locate", "locating", "remember", "remembering",
    "query", "filter", "sort", "tag", "label",
    "face", "facial", "recognition", "people", "person",
    "place", "location", "where", "gps", "map",
    "date", "year", "month", "old photo", "old picture",
    "event", "trip", "vacation", "wedding", "birthday", "party",
    "object", "car", "dog", "cat", "food", "beach", "mountain",
    "duplicate", "similar", "same photo",
    "ask photos", "ai search", "gemini",
    "organize", "album", "category",
    "retrieve", "retrieval", "keyword",
    "wish", "hope", "should", "would be nice", "feature request",
    "accurate", "accuracy", "relevant", "irrelevant", "wrong result",
    "thousands of photos", "too many photos", "large library",
    "tip of my tongue", "vague", "fuzzy", "hazy",
    "workaround", "trick", "hack",
]

# Keywords that indicate a post is NOT about retrieval
EXCLUDE_KEYWORDS = [
    "storage plan", "subscription", "pricing", "15gb", "100gb",
    "backup failed", "sync error", "upload stuck",
    "login", "sign in", "account locked",
    "editor", "editing", "crop", "rotate", "enhance",
    "print", "photo book", "canvas",
    "sharing link", "shared album permission",
]

# Themes to auto-tag
THEME_PATTERNS = {
    "Search accuracy": ["accurate", "accuracy", "relevant", "irrelevant", "wrong result", "doesn't find", "can't find", "not finding"],
    "Face/people search": ["face", "facial", "recognition", "people", "person", "who is"],
    "Location/place search": ["location", "place", "where", "gps", "map", "city", "country"],
    "Time-based search": ["date", "year", "month", "old photo", "old picture", "years ago", "last year"],
    "Event/activity search": ["event", "trip", "vacation", "wedding", "birthday", "party", "activity"],
    "Object/scene search": ["object", "car", "dog", "cat", "food", "beach", "mountain", "sunset", "flower"],
    "Scrolling fatigue": ["scroll", "scrolling", "thousands", "too many", "large library", "manual"],
    "AI/Ask Photos": ["ask photos", "ai search", "gemini", "ai", "artificial intelligence", "smart search"],
    "Natural language search": ["natural language", "describe", "description", "contextual", "vague", "fuzzy", "hazy", "remember"],
    "Duplicate/similar photos": ["duplicate", "similar", "same photo", "identical"],
    "Workarounds": ["workaround", "trick", "hack", "tip", "instead I"],
    "Feature request": ["wish", "hope", "should", "would be nice", "feature request", "please add", "need a way"],
    "Organization/albums": ["organize", "album", "category", "folder", "tag", "label"],
    "Positive experience": ["love the search", "amazing search", "great feature", "works well", "found it", "so easy to find"],
}


def fetch_reddit_posts_apify(
    api_token: str, 
    subreddit_name: str, 
    limit: int
) -> list[dict]:
    logger.info("Apify Reddit scraper: starting — target %d posts from r/%s.", limit, subreddit_name)

    client = ApifyClient(api_token)

    run_input = {
        "startUrls": [
            {"url": f"https://www.reddit.com/r/{subreddit_name}/hot/"}
        ],
        "maxItems": limit,
        "skipComments": True,
        "proxy": {
            "useApifyProxy": True
        }
    }

    all_entries: list[dict] = []
    
    try:
        logger.info("Starting Apify Actor automation-lab/reddit-scraper...")
        run_obj = client.actor("automation-lab/reddit-scraper").call(run_input=run_input)
        
        # In apify-client >= 1.0, call() returns a Run object which has a default_dataset_id attribute
        dataset_id = getattr(run_obj, 'default_dataset_id', None)
        if not dataset_id and hasattr(run_obj, 'get'): # Fallback for older dicts
            dataset_id = run_obj.get("defaultDatasetId")
            
        logger.info("Actor finished. Fetching dataset items... (Dataset ID: %s)", dataset_id)
        dataset_items = client.dataset(dataset_id).iterate_items()
        
        for item in dataset_items:
            created_at = item.get("createdAt") or item.get("created_utc")
            if isinstance(created_at, (int, float)):
                created_utc = datetime.fromtimestamp(created_at, tz=timezone.utc).isoformat()
            elif isinstance(created_at, str):
                created_utc = created_at
            else:
                created_utc = datetime.now(timezone.utc).isoformat()
            
            mapped = {
                "source": "reddit",
                "post_id": str(item.get("id", "")),
                "subreddit": item.get("subreddit", subreddit_name),
                "post_title": item.get("title", ""),
                "post_body": item.get("text") or item.get("body") or item.get("selftext") or "",
                "score": item.get("upvotes") or item.get("score") or 0,
                "author": item.get("username") or item.get("author") or "[deleted]",
                "created_utc": created_utc,
                "url": item.get("url", f"https://www.reddit.com/r/{subreddit_name}"),
                "num_comments": item.get("numComments") or item.get("num_comments") or 0
            }
            all_entries.append(mapped)
            
    except Exception as exc:
        logger.error("Apify Reddit scraper error: %s", exc)

    logger.info("Reddit scraper: collected %d raw entries.", len(all_entries))
    return all_entries


def is_relevant(title: str, text: str) -> bool:
    """Check if a post is related to photo retrieval."""
    t = (title + " " + text).lower()

    if not any(kw in t for kw in INCLUDE_KEYWORDS):
        return False

    exclude_hits = sum(1 for kw in EXCLUDE_KEYWORDS if kw in t)
    include_hits = sum(1 for kw in INCLUDE_KEYWORDS if kw in t)

    if exclude_hits > include_hits:
        return False

    try:
        if detect(t) != "en":
            return False
    except LangDetectException:
        return False

    return True


def detect_themes(title: str, text: str) -> list[str]:
    """Auto-detect themes from a post."""
    t = (title + " " + text).lower()
    themes = []
    for theme, patterns in THEME_PATTERNS.items():
        if any(p in t for p in patterns):
            themes.append(theme)
    return themes if themes else ["General retrieval"]


def detect_sentiment(title: str, text: str) -> str:
    """Simple rule-based sentiment."""
    t = (title + " " + text).lower()
    pos = ["love", "great", "amazing", "awesome", "works well", "easy to find", "found it", "helpful", "thank"]
    neg = ["can't find", "cannot find", "doesn't work", "broken", "useless", "terrible", "frustrat", "annoying", "hate", "worst", "bug"]

    pos_hits = sum(1 for p in pos if p in t)
    neg_hits = sum(1 for n in neg if n in t)

    if pos_hits > neg_hits:
        return "positive"
    elif neg_hits > pos_hits:
        return "negative"
    return "mixed"


def run() -> list[dict]:
    api_token = os.getenv("APIFY_API_TOKEN")
    subreddit_name = os.getenv("REDDIT_SUBREDDIT", "googlephotos")
    limit = int(os.getenv("REDDIT_POST_LIMIT", "100"))
    
    if not api_token:
        logger.error("Reddit scraper FAILED. APIFY_API_TOKEN is missing from .env.")
        return []
    
    start = time.time()
    
    # === Step 1: Fetch Raw Posts ===
    all_entries = fetch_reddit_posts_apify(api_token, subreddit_name, limit)

    # Save raw
    RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_OUTPUT, "w", encoding="utf-8") as fh:
        json.dump(all_entries, fh, indent=2, ensure_ascii=False)
    logger.info("Raw: %d total posts saved to %s", len(all_entries), RAW_OUTPUT)

    # === Step 2: Filter and structure ===
    filtered = []
    for entry in all_entries:
        if not is_relevant(entry["post_title"], entry["post_body"]):
            continue

        themes = detect_themes(entry["post_title"], entry["post_body"])
        sentiment = detect_sentiment(entry["post_title"], entry["post_body"])

        filtered.append({
            "source": "reddit",
            "post_id": entry["post_id"],
            "subreddit": entry["subreddit"],
            "post_title": entry["post_title"],
            "post_body": entry["post_body"],
            "created_utc": entry["created_utc"],
            "author": entry["author"],
            "score": entry["score"],
            "num_comments": entry["num_comments"],
            "url": entry["url"],
            "themes": themes,
            "sentiment": sentiment,
        })

    # Save filtered
    FILTERED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(FILTERED_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)

    logger.info("Filtered: %d relevant posts saved to %s", len(filtered), FILTERED_OUTPUT)

    # Print summary
    theme_counts = {}
    for r in filtered:
        for t in r["themes"]:
            theme_counts[t] = theme_counts.get(t, 0) + 1

    logger.info("=== Theme Distribution ===")
    for theme, count in sorted(theme_counts.items(), key=lambda x: -x[1]):
        logger.info("  %s: %d", theme, count)

    elapsed = time.time() - start
    logger.info("Reddit processing complete in %.1fs.", elapsed)
    return filtered

if __name__ == "__main__":
    run()
