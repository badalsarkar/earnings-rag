"""FastAPI application exposing the transcripts table over HTTP."""
from fastapi import FastAPI, HTTPException

from ..config import configure_logging, load_env
from ..db import get_transcript, get_transcripts_by_ticker, upsert_transcript
from .schemas import TranscriptIn, TranscriptOut

load_env()
configure_logging()

app = FastAPI(title="Earnings RAG API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.put("/transcripts", response_model=TranscriptOut)
def create_transcript(body: TranscriptIn):
    row = upsert_transcript(
        body.ticker, body.quarter, body.fiscal_year, body.report_date, body.content
    )
    return _serialize(row)


@app.get("/transcripts/{ticker}", response_model=list[TranscriptOut])
def list_transcripts(ticker: str):
    rows = get_transcripts_by_ticker(ticker.upper())
    return [_serialize(r) for r in rows]


@app.get("/transcripts/{ticker}/q{quarter}/{fiscal_year}", response_model=TranscriptOut)
def read_transcript(ticker: str, quarter: int, fiscal_year: int):
    row = get_transcript(ticker.upper(), quarter, fiscal_year)
    if row is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return _serialize(row)


def _serialize(row: dict) -> dict:
    return {**row, "created_at": str(row["created_at"]), "updated_at": str(row["updated_at"])}
