from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import json
import os
from typing import List, Dict, Any

app = FastAPI(title="Discovery Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for the parsed dataset
DATASET: List[Dict[str, Any]] = []

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    global DATASET
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and JSON files are supported.")
            
        # Clean and normalize (basic)
        df = df.dropna(how="all")
        DATASET = df.to_dict(orient="records")
        return {"status": "success", "rows_processed": len(DATASET)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/overview")
async def get_overview():
    if not DATASET:
        return {"total_records": 0, "relevant_records": 0}
        
    df = pd.DataFrame(DATASET)
    
    total = len(df)
    sources = df["source"].value_counts().to_dict() if "source" in df.columns else {}
    
    return {
        "total_records": total,
        "sources": sources
    }

@app.get("/api/data")
async def get_data():
    return DATASET

# Add more robust endpoints later for Groq AI extraction
