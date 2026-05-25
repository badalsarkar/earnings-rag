from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import db_service

app = FastAPI(title="Earnings RAG API")


class TranscriptIn(BaseModel):
    ticker: str
    quarter: int
    fiscal_year: int
    report_date: date
    content: str


class TranscriptOut(BaseModel):
    id: int
    ticker: str
    quarter: int
    fiscal_year: int
    report_date: date
    content: str | None
    created_at: str
    updated_at: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.put("/transcripts", response_model=TranscriptOut)
def upsert_transcript(body: TranscriptIn):
    row = db_service.upsert_transcript(
        body.ticker, body.quarter, body.fiscal_year, body.report_date, body.content
    )
    return _serialize(row)


@app.get("/transcripts/{ticker}", response_model=list[TranscriptOut])
def list_transcripts(ticker: str):
    rows = db_service.get_transcripts_by_ticker(ticker.upper())
    return [_serialize(r) for r in rows]


@app.get("/transcripts/{ticker}/q{quarter}/{fiscal_year}", response_model=TranscriptOut)
def get_transcript(ticker: str, quarter: int, fiscal_year: int):
    row = db_service.get_transcript(ticker.upper(), quarter, fiscal_year)
    if row is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return _serialize(row)


def _serialize(row: dict) -> dict:
    return {**row, "created_at": str(row["created_at"]), "updated_at": str(row["updated_at"])}
