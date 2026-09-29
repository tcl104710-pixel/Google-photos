"""api/main.py — FastAPI application entry point (skeleton for Phase 4)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import auth, session, user
import api.dependencies as deps

app = FastAPI(
    title="Photo Retrieval MVP",
    description="AI-native photo retrieval using incomplete or vague memories",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

import os
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins + ["*"], # For demo purposes, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(user.router, prefix="/api")

@app.get("/api/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
