"""Request/response models for the HTTP API."""
from datetime import date

from pydantic import BaseModel


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
