"""Request/response models for the HTTP API."""
from datetime import date

from pydantic import BaseModel, Field

from ..retrieval import DEFAULT_TOP_K


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


class EmbedIn(BaseModel):
    ticker: str
    quarter: int
    fiscal_year: int


class EmbedOut(BaseModel):
    """Result of embedding a single transcript."""

    ticker: str
    quarter: int
    fiscal_year: int
    chunks_embedded: int


class SearchIn(BaseModel):
    query: str
    # Upper bound is a guard on embedding + query cost, not a storage limit.
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=50)


class ChunkOut(BaseModel):
    """One retrieved chunk, carrying the transcript it came from."""

    id: int
    transcript_id: int
    chunk_index: int
    content: str
    similarity: float
    ticker: str
    quarter: int
    fiscal_year: int
    report_date: date


class ChatIn(BaseModel):
    query: str = Field(min_length=1)
    # Upper bound is a guard on embedding + query cost, not a storage limit.
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=50)


class CitationOut(BaseModel):
    start: int
    end: int
    text: str
    sources: list[str]


class ChatOut(BaseModel):
    """A generated answer, its supporting citations, and the chunks it was grounded in."""

    answer: str
    citations: list[CitationOut]
    chunks: list[ChunkOut]
