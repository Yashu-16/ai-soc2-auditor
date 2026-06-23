"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import upload, analyze

app = FastAPI(
    title="AI SOC2 Auditor",
    description="Simulated SOC2 audit engine for SaaS infrastructure signals.",
    version="0.1.0",
)

# CORS: allow the local Vite dev server to call this API during development.
# In production, this should be restricted to the actual deployed frontend
# origin rather than left wide open — flagged here intentionally as a
# known dev-vs-prod tradeoff.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, tags=["ingestion"])
app.include_router(analyze.router, tags=["analysis"])


@app.get("/health")
def health_check():
    return {"status": "ok"}