"""FastAPI application exposing the transcripts table over HTTP."""
from cohere.core.api_error import ApiError
from fastapi import FastAPI, HTTPException

from ..chat import answer as answer_chat
from ..config import configure_logging, load_env
from ..db import get_transcript, get_transcripts_by_ticker, upsert_transcript
from ..ingest.embed import embed_transcript
from ..retrieval import retrieve
from .schemas import (
    ChatIn,
    ChatOut,
    ChunkOut,
    EmbedIn,
    EmbedOut,
    SearchIn,
    TranscriptIn,
    TranscriptOut,
)

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


@app.post("/transcripts/embed", response_model=EmbedOut)
def embed_one(body: EmbedIn):
    """Chunk and embed one transcript's content, upserting its vectors."""
    row = get_transcript(body.ticker.upper(), body.quarter, body.fiscal_year)
    if row is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    if not row["content"]:
        raise HTTPException(status_code=422, detail="Transcript has no content")
    try:
        chunk_count = embed_transcript(row)
    except ApiError as exc:
        # embed_transcript is all-or-nothing, so no chunks were written.
        raise HTTPException(status_code=502, detail="Embedding call failed") from exc
    return {
        "ticker": row["ticker"],
        "quarter": row["quarter"],
        "fiscal_year": row["fiscal_year"],
        "chunks_embedded": chunk_count,
    }


@app.post("/search", response_model=list[ChunkOut])
def search(body: SearchIn):
    """Return the chunks most similar to `query`, closest first.

    POST rather than GET because the query is free-form natural language that
    can run long; an empty query yields an empty list, not an error.
    """
    return retrieve(body.query, top_k=body.top_k)


@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    """Answer `query`, grounded in the transcript chunks most relevant to it."""
    return answer_chat(body.query, top_k=body.top_k)


def _serialize(row: dict) -> dict:
    return {**row, "created_at": str(row["created_at"]), "updated_at": str(row["updated_at"])}
