"""scrapers/youtube_scraper.py — YouTube comment ingestion.

Fetches YouTube comments using the YouTube Data API.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

RAW_YOUTUBE_PATH = Path("data/raw/raw_youtube.json")

def fetch_youtube_comments(api_key: str, video_id: str, max_comments: int = 100) -> list[dict]:
    logger.info("YouTube scraper: starting — target video %s.", video_id)

    youtube = build("youtube", "v3", developerKey=api_key)
    all_comments: list[dict] = []
    
    try:
        # Fetch video title first
        video_resp = youtube.videos().list(part="snippet", id=video_id).execute()
        if not video_resp.get("items"):
            logger.error("YouTube scraper: Video %s not found.", video_id)
            return []
        
        video_title = video_resp["items"][0]["snippet"]["title"]
        
        next_page_token = None
        
        while len(all_comments) < max_comments:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_comments - len(all_comments)),
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()
            
            for item in response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                mapped = {
                    "source": "youtube",
                    "video_id": video_id,
                    "video_title": video_title,
                    "comment_id": item["id"],
                    "author": comment.get("authorDisplayName", ""),
                    "text": comment.get("textDisplay", ""),
                    "likes": comment.get("likeCount", 0),
                    "published_at": comment.get("publishedAt", ""),
                    "reply_count": item["snippet"].get("totalReplyCount", 0),
                }
                all_comments.append(mapped)
                
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
                
            time.sleep(1) # politeness delay
            
    except HttpError as exc:
        logger.error("YouTube scraper API error: %s", exc)
    except Exception as exc:
        logger.error("YouTube scraper unexpected error: %s", exc)

    logger.info("YouTube scraper: collected %d comments.", len(all_comments))
    return all_comments

def run() -> list[dict]:
    api_key = os.getenv("YOUTUBE_API_KEY")
    video_id = os.getenv("YOUTUBE_VIDEO_ID")
    
    if not api_key or not video_id:
        logger.error("YouTube scraper FAILED. YOUTUBE_API_KEY or YOUTUBE_VIDEO_ID is missing.")
        return []
    
    start = time.time()
    comments = fetch_youtube_comments(api_key=api_key, video_id=video_id)

    RAW_YOUTUBE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_YOUTUBE_PATH, "w", encoding="utf-8") as fh:
        json.dump(comments, fh, indent=2, ensure_ascii=False, default=str)

    elapsed = time.time() - start
    logger.info("YouTube: %d comments written to %s in %.1fs.", len(comments), RAW_YOUTUBE_PATH, elapsed)
    return comments

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run()
