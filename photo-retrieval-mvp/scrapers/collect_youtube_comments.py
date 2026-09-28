"""scrapers/collect_youtube_comments.py — YouTube comment collection for photo retrieval research.

Searches for relevant Google Photos videos, fetches their comments,
and filters for photo-retrieval-related discussions using keyword matching.
No LLM required — pure keyword + heuristic filtering.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from langdetect import detect, LangDetectException

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

RAW_OUTPUT = Path("data/raw/raw_youtube_comments.json")
FILTERED_OUTPUT = Path("data/processed/youtube_search_comments.json")

# Videos to search for — queries that surface Google Photos search/retrieval content
SEARCH_QUERIES = [
    "Google Photos search tips",
    "Google Photos find old photos",
    "Google Photos Ask Photos AI",
    "Google Photos search not working",
    "how to find photos in Google Photos",
    "Google Photos search features",
    "Google Photos tips and tricks search",
    "Google Photos face recognition search",
    "Google Photos search by location",
    "find specific photo Google Photos",
]

# Keywords that indicate a comment is about photo retrieval
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

# Keywords that indicate a comment is NOT about retrieval
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


def search_videos(youtube, queries: list[str], max_per_query: int = 5) -> list[dict]:
    """Search YouTube for relevant videos and return unique video metadata."""
    seen_ids = set()
    videos = []

    for query in queries:
        logger.info("Searching YouTube for: '%s'", query)
        try:
            resp = youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_per_query,
                order="relevance",
                relevanceLanguage="en",
            ).execute()

            for item in resp.get("items", []):
                vid = item["id"]["videoId"]
                if vid not in seen_ids:
                    seen_ids.add(vid)
                    videos.append({
                        "video_id": vid,
                        "title": item["snippet"]["title"],
                        "channel": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"],
                    })
        except HttpError as e:
            logger.error("Search failed for '%s': %s", query, e)

        time.sleep(0.5)

    logger.info("Found %d unique videos across %d queries.", len(videos), len(queries))
    return videos


def fetch_comments(youtube, video_id: str, video_title: str, max_comments: int = 200) -> list[dict]:
    """Fetch top-level comments for a single video."""
    comments = []
    next_page = None

    while len(comments) < max_comments:
        try:
            resp = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_comments - len(comments)),
                pageToken=next_page,
                textFormat="plainText",
                order="relevance",
            ).execute()
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning("Comments disabled for video %s (%s)", video_id, video_title)
            else:
                logger.error("Comment fetch error for %s: %s", video_id, e)
            break

        for item in resp.get("items", []):
            snip = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "source": "youtube",
                "video_id": video_id,
                "video_title": video_title,
                "comment_id": item["id"],
                "author": snip.get("authorDisplayName", ""),
                "text": snip.get("textDisplay", ""),
                "likes": snip.get("likeCount", 0),
                "published_at": snip.get("publishedAt", ""),
                "reply_count": item["snippet"].get("totalReplyCount", 0),
            })

        next_page = resp.get("nextPageToken")
        if not next_page:
            break
        time.sleep(0.5)

    return comments


def is_relevant(text: str) -> bool:
    """Check if a comment is related to photo retrieval."""
    t = text.lower()

    # Must contain at least one inclusion keyword
    if not any(kw in t for kw in INCLUDE_KEYWORDS):
        return False

    # Must NOT be dominated by exclusion topics
    exclude_hits = sum(1 for kw in EXCLUDE_KEYWORDS if kw in t)
    include_hits = sum(1 for kw in INCLUDE_KEYWORDS if kw in t)

    # If more exclude hits than include hits, skip
    if exclude_hits > include_hits:
        return False

    # Language check
    try:
        if detect(t) != "en":
            return False
    except LangDetectException:
        return False

    # Minimum length filter — very short comments rarely have substance
    if len(text.split()) < 5:
        return False

    return True


def detect_themes(text: str) -> list[str]:
    """Auto-detect themes from a comment."""
    t = text.lower()
    themes = []
    for theme, patterns in THEME_PATTERNS.items():
        if any(p in t for p in patterns):
            themes.append(theme)
    return themes if themes else ["General retrieval"]


def detect_sentiment(text: str) -> str:
    """Simple rule-based sentiment."""
    t = text.lower()
    pos = ["love", "great", "amazing", "awesome", "works well", "easy to find", "found it", "helpful", "thank"]
    neg = ["can't find", "cannot find", "doesn't work", "broken", "useless", "terrible", "frustrat", "annoying", "hate", "worst"]

    pos_hits = sum(1 for p in pos if p in t)
    neg_hits = sum(1 for n in neg if n in t)

    if pos_hits > neg_hits:
        return "positive"
    elif neg_hits > pos_hits:
        return "negative"
    return "mixed"


def main():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        logger.error("YOUTUBE_API_KEY not set. Please set it in your .env file.")
        return

    youtube = build("youtube", "v3", developerKey=api_key)

    # === Step 1: Search for relevant videos ===
    videos = search_videos(youtube, SEARCH_QUERIES, max_per_query=5)

    # === Step 2: Fetch comments from all videos ===
    all_comments = []
    for i, video in enumerate(videos):
        logger.info("[%d/%d] Fetching comments for: %s", i + 1, len(videos), video["title"])
        comments = fetch_comments(youtube, video["video_id"], video["title"], max_comments=200)
        all_comments.extend(comments)
        logger.info("  → %d comments fetched (total: %d)", len(comments), len(all_comments))
        time.sleep(1)

    # Save raw
    RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_comments, f, indent=2, ensure_ascii=False)
    logger.info("Raw: %d total comments saved to %s", len(all_comments), RAW_OUTPUT)

    # === Step 3: Filter and structure ===
    filtered = []
    for comment in all_comments:
        text = comment.get("text", "")
        if not is_relevant(text):
            continue

        themes = detect_themes(text)
        sentiment = detect_sentiment(text)

        filtered.append({
            "source": "youtube",
            "video_id": comment["video_id"],
            "video_title": comment["video_title"],
            "comment_text": text,
            "comment_date": comment["published_at"],
            "author": comment["author"],
            "likes": comment["likes"],
            "themes": themes,
            "sentiment": sentiment,
        })

    # Save filtered
    FILTERED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(FILTERED_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)

    logger.info("Filtered: %d relevant comments saved to %s", len(filtered), FILTERED_OUTPUT)

    # Print summary
    theme_counts = {}
    for r in filtered:
        for t in r["themes"]:
            theme_counts[t] = theme_counts.get(t, 0) + 1

    logger.info("=== Theme Distribution ===")
    for theme, count in sorted(theme_counts.items(), key=lambda x: -x[1]):
        logger.info("  %s: %d", theme, count)


if __name__ == "__main__":
    main()
