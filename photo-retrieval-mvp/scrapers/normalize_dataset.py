import json
import csv
import uuid
import re
from pathlib import Path
from langdetect import detect, LangDetectException

RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/output")
FINAL_CSV = OUTPUT_DIR / "normalized_combined_feedback.csv"

# Keywords used in the existing scrapers to identify photo retrieval topics
INCLUDE_KEYWORDS = [
    "search", "find", "finding", "found", "look", "looking", "scroll", "scrolling",
    "locate", "locating", "remember", "query", "sort", "filter", "tag", "face",
    "people", "where", "lost", "organize", "retrieve", "retrieving", "ask photos", "ai",
]

EXCLUDE_KEYWORDS = [
    "sync", "backup", "download", "upload", "storage", "full", "space", "pay", 
    "price", "cost", "money", "subscription", "crash", "freeze", "bug", "glitch",
    "login", "password", "account", "print", "canvas", "book"
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Remove unnecessary whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_relevant(text: str) -> bool:
    if not text:
        return False
    
    t = text.lower()
    
    # 1. Must contain at least one inclusion keyword
    if not any(kw in t for kw in INCLUDE_KEYWORDS):
        return False
        
    # 2. Check exclusion vs inclusion hits
    include_hits = sum(1 for kw in INCLUDE_KEYWORDS if kw in t)
    exclude_hits = sum(1 for kw in EXCLUDE_KEYWORDS if kw in t)
    
    if exclude_hits > include_hits:
        return False
        
    # 3. Minimum length (too short = probably spam or useless)
    words = text.split()
    if len(words) < 4:
        return False
        
    # 4. English only
    try:
        if detect(t) != "en":
            return False
    except LangDetectException:
        return False
        
    return True

def process_playstore(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return []
    
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            text = clean_text(item.get("content", ""))
            if is_relevant(text):
                records.append({
                    "id": str(uuid.uuid4()),
                    "source": "play_store" if item.get("source") == "playstore" else "play_store", # Map to requested play_store
                    "text": text,
                    "date": str(item.get("at", "")),
                    "rating": item.get("score"),
                    "author": None,
                    "url": None
                })
    return records

def process_youtube(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return []
    
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            text = clean_text(item.get("text", ""))
            if is_relevant(text):
                records.append({
                    "id": str(uuid.uuid4()),
                    "source": "youtube",
                    "text": text,
                    "date": item.get("published_at", ""),
                    "rating": None,
                    "author": item.get("author"),
                    "url": f"https://youtube.com/watch?v={item.get('video_id')}&lc={item.get('comment_id')}" if item.get("video_id") else None
                })
    return records

def process_reddit(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return []
    
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            text = clean_text(item.get("post_title", "") + " " + item.get("post_body", ""))
            if is_relevant(text):
                records.append({
                    "id": str(uuid.uuid4()),
                    "source": "reddit",
                    "text": text,
                    "date": item.get("created_utc", ""),
                    "rating": None, # Upvotes could go here but instructions say "rating = Play Store rating when available; otherwise null"
                    "author": item.get("author"),
                    "url": item.get("url")
                })
    return records

def run():
    print("Starting normalization pipeline...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    playstore_file = RAW_DIR / "large_raw_playstore.json"
    youtube_file = RAW_DIR / "raw_youtube_comments.json"
    reddit_file = RAW_DIR / "raw_reddit.json"
    
    # Process all sources
    playstore_records = process_playstore(playstore_file)
    youtube_records = process_youtube(youtube_file)
    reddit_records = process_reddit(reddit_file)
    
    initial_ps = len(playstore_records)
    initial_yt = len(youtube_records)
    initial_rd = len(reddit_records)
    
    all_records = playstore_records + youtube_records + reddit_records
    
    # Deduplicate by exact text
    seen_texts = set()
    deduped_records = []
    duplicates = 0
    
    for r in all_records:
        t = r["text"].lower()
        if t in seen_texts:
            duplicates += 1
            continue
        seen_texts.add(t)
        deduped_records.append(r)
        
    # Write to CSV
    fields = ["id", "source", "text", "date", "rating", "author", "url"]
    with open(FINAL_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(deduped_records)
        
    # Re-calculate final numbers after deduplication
    final_ps = sum(1 for r in deduped_records if r["source"] == "play_store")
    final_yt = sum(1 for r in deduped_records if r["source"] == "youtube")
    final_rd = sum(1 for r in deduped_records if r["source"] == "reddit")
    
    # Calculate empty/invalid (would be skipped during is_relevant check, but let's approximate based on raw sizes)
    # Actually, we can just print the exact requested stats.
    
    with open(playstore_file, 'r', encoding='utf-8') as f: ps_raw = len(json.load(f))
    with open(youtube_file, 'r', encoding='utf-8') as f: yt_raw = len(json.load(f))
    with open(reddit_file, 'r', encoding='utf-8') as f: rd_raw = len(json.load(f))
    
    total_raw = ps_raw + yt_raw + rd_raw
    total_invalid = total_raw - initial_ps - initial_yt - initial_rd
    
    print(f"Play Store records collected: {ps_raw}")
    print(f"YouTube records collected: {yt_raw}")
    print(f"Reddit records collected: {rd_raw}")
    print(f"Records removed as duplicates: {duplicates}")
    print(f"Records removed as empty/invalid (spam/irrelevant/non-English): {total_invalid}")
    print(f"Final Play Store records: {final_ps}")
    print(f"Final YouTube records: {final_yt}")
    print(f"Final Reddit records: {final_rd}")
    print(f"Total final records: {len(deduped_records)}")
    print(f"Exact file path: {FINAL_CSV.absolute()}")
    
    print("\n--- 5 Sample Rows ---")
    import random
    if len(deduped_records) >= 5:
        samples = random.sample(deduped_records, 5)
        for s in samples:
            print(s)

if __name__ == "__main__":
    run()
