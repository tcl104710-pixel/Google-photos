import os
import json
import asyncio
import csv
from pydantic import BaseModel, Field
from typing import List, Optional
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../photo-retrieval-mvp/.env'))

class AnalysisResult(BaseModel):
    relevance: str = Field(description="Relevant, Not Relevant, or Unclear")
    scenario: List[str] = Field(description="Travel, Family, Friends, Wedding, Documents, etc")
    remembered: List[str] = Field(description="Person, Relationship, Place, Event, Activity, Object, Emotion, etc")
    forgotten: List[str] = Field(description="Exact date, Exact location, Filename, etc")
    search_behavior: List[str] = Field(description="Keywords, Natural language, Date search, Browsed manually, etc")
    failure_point: str = Field(description="Memory expression, Query formation, System understanding, Candidate retrieval, Result evaluation, Successful retrieval, Other")
    workaround: str = Field(description="Any workaround used (e.g., scrolled manually, used desktop app)")
    outcome: str = Field(description="Successful retrieval, Partial success, Failed retrieval, Abandoned search, Unclear")

SYSTEM_PROMPT = """You are an expert UX Researcher analyzing Google Photos user feedback.
Analyze the user's feedback and extract structured information about their photo retrieval journey.
If the feedback is NOT about trying to find/retrieve an old photo (e.g., backup issues, crashes), mark relevance as 'Not Relevant' and leave other fields empty.
Be extremely precise."""

async def process_record(client, record):
    try:
        response = await client.chat.completions.create(
            model="llama3-70b-8192", # Using 70b or 8b for speed
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Source: {record.get('source')}\nFeedback: {record.get('text')}"}
            ],
            response_format={"type": "json_schema", "json_schema": {"name": "analysis", "schema": AnalysisResult.model_json_schema()}},
            temperature=0
        )
        result = json.loads(response.choices[0].message.content)
        return {**record, "analysis": result}
    except Exception as e:
        print(f"Error processing record {record.get('id')}: {e}")
        return {**record, "analysis": {"relevance": "Error"}}

async def main():
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    
    input_file = "../../photo-retrieval-mvp/data/output/normalized_combined_feedback.csv"
    output_file = "data/processed_discovery.json"
    
    os.makedirs("data", exist_ok=True)
    
    records = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)
        
    print(f"Loaded {len(records)} records. Sampling top 100 for speed...")
    # Process only 100 to save time and API rate limits
    records = records[:100]
    
    tasks = [process_record(client, r) for r in records]
    
    results = []
    chunk_size = 20
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        chunk_results = await asyncio.gather(*chunk)
        results.extend(chunk_results)
        print(f"Processed {len(results)} / {len(tasks)}")
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
        
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
