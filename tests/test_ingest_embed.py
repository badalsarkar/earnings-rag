"""Behavior of the transcript-embedding batch job.

Chunking and the Cohere call are stubbed at the module seam so these tests
exercise the atomicity and error-handling in embed_all/embed_transcript
without touching the network or the database: a transcript whose embed call
fails must be dropped whole, with no chunks written, and the run must
continue on to the remaining transcripts.
"""
import pytest
from cohere.core.api_error import ApiError

from earnings_rag.ingest import embed as embed_module

TRANSCRIPTS = [
    {"id": 1, "ticker": "MSFT", "quarter": 3, "fiscal_year": 2024, "content": "hello"},
    {"id": 2, "ticker": "GOOGL", "quarter": 1, "fiscal_year": 2025, "content": "world"},
]


@pytest.fixture
def upserts(monkeypatch):
    calls = []
    monkeypatch.setattr(embed_module, "get_all_transcripts", lambda: TRANSCRIPTS)
    monkeypatch.setattr(embed_module, "chunk_text", lambda content: [content])
    monkeypatch.setattr(
        embed_module,
        "upsert_transcript_chunks",
        lambda transcript_id, chunks, embeddings: calls.append(transcript_id),
    )
    return calls


def test_embed_all_upserts_once_per_transcript_on_success(upserts, monkeypatch):
    monkeypatch.setattr(embed_module, "embed", lambda chunks: [[0.0] for _ in chunks])

    embed_module.embed_all()

    assert upserts == [1, 2]


def test_embed_all_drops_a_transcript_whose_embed_call_fails(upserts, monkeypatch):
    def flaky_embed(chunks):
        if chunks == ["hello"]:
            raise ApiError(status_code=429, body="rate limited")
        return [[0.0] for _ in chunks]

    monkeypatch.setattr(embed_module, "embed", flaky_embed)

    embed_module.embed_all()

    assert upserts == [2]
