import os
import sys
import csv
import json
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm.groq_client import GroqClient
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path("data/output/normalized_combined_feedback.csv")
OUTPUT_MD = Path("data/output/research_insights.md")

SYSTEM_PROMPT = """You are an expert UX Researcher and Data Analyst specializing in photo retrieval and digital memory.
You are given a dataset of real user feedback (App Store reviews, Play Store reviews, YouTube comments, and Reddit posts) regarding Google Photos.

Your goal is to perform a deep thematic synthesis of this feedback to answer the following specific research questions:
1. What kinds of old photos do users struggle to retrieve? (Categorize the types of photos/events/subjects)
2. What information do people actually remember about a photo? (Context, visual details, emotions, people, objects, etc.)
3. What information have they forgotten? (Dates, exact locations, file names, etc.)
4. How do users formulate searches when their memory is incomplete? (What workarounds or natural language strategies do they use?)

INSTRUCTIONS FOR SYNTHESIS:
- Go beyond simple summarization. Identify distinct retrieval problems and opportunity areas.
- Use direct quotes from the provided data as evidence for your claims (cite the source platform).
- Structure your response using markdown headers, bullet points, and bold text for readability.
- Be highly analytical. Compare different types of struggles (e.g., struggling to find a specific document vs. struggling to find a photo from a specific childhood event).
"""

async def synthesize_data():
    if not CSV_PATH.exists():
        print("CSV not found.")
        return

    # Read all texts
    feedback_entries = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Format nicely for the LLM
            entry = f"[{row['source'].upper()}] {row['text']}"
            feedback_entries.append(entry)

    print(f"Loaded {len(feedback_entries)} feedback entries.")
    
    # We might need to chunk if the context limit is small, but OpenAI/Groq 120b usually handles 8k-32k tokens.
    # 516 short reviews is roughly 10,000 to 15,000 words (~20,000 tokens).
    # To respect the 8000 TPM limit on Groq's OSS model, we will take the top 50 entries
    feedback_entries.sort(key=lambda x: len(x), reverse=True)
    top_entries = feedback_entries[:50]
    
    combined_text = "\n".join(top_entries)
    
    client = GroqClient()
    
    print("Sending data to LLM for thematic synthesis. This may take a minute...")
    
    user_message = f"Here is the dataset of user feedback:\n\n{combined_text}\n\nBased ONLY on this data, provide the comprehensive UX research synthesis."
    
    try:
        report = await client.generate_text(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
            temperature=0.2
        )
        
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_MD, "w", encoding="utf-8") as f:
            f.write(report)
            
        print(f"\nSynthesis complete! Report saved to {OUTPUT_MD.absolute()}")
        
    except Exception as e:
        print(f"Error during LLM generation: {e}")

if __name__ == "__main__":
    asyncio.run(synthesize_data())
