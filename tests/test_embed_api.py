"""HTTP behavior of the per-transcript embed endpoint.

Chunking/embedding itself is exercised in the ingest layer; what matters here
is the contract at the edge — which transcript gets looked up, what's rejected
before any Cohere call is paid for, and what comes back.
"""
import sys

import pytest
from cohere.core.api_error import ApiError
from fastapi.testclient import TestClient

from earnings_rag.api import app

app_module = sys.modules["earnings_rag.api.app"]

TRANSCRIPT = {
    "id": 42,
    "ticker": "MSFT",
    "quarter": 3,
    "fiscal_year": 2024,
    "content": "Cloud revenue grew 31% year over year.",
}


@pytest.fixture
def client(monkeypatch):
    """A client backed by a stub transcript lookup and a stub embedder."""

    def fake_get_transcript(ticker: str, quarter: int, fiscal_year: int) -> dict | None:
        if (ticker, quarter, fiscal_year) == ("MSFT", 3, 2024):
            return TRANSCRIPT
        return None

    monkeypatch.setattr(app_module, "get_transcript", fake_get_transcript)
    monkeypatch.setattr(app_module, "embed_transcript", lambda transcript: 3)
    return TestClient(app)


def test_embed_returns_the_chunk_count(client):
    response = client.post(
        "/transcripts/embed", json={"ticker": "MSFT", "quarter": 3, "fiscal_year": 2024}
    )

    assert response.status_code == 200
    assert response.json() == {
        "ticker": "MSFT", "quarter": 3, "fiscal_year": 2024, "chunks_embedded": 3,
    }


def test_embed_is_case_insensitive_on_ticker(client):
    response = client.post(
        "/transcripts/embed", json={"ticker": "msft", "quarter": 3, "fiscal_year": 2024}
    )

    assert response.status_code == 200


def test_embed_404s_for_an_unknown_transcript(client):
    response = client.post(
        "/transcripts/embed", json={"ticker": "GOOGL", "quarter": 1, "fiscal_year": 2025}
    )

    assert response.status_code == 404


def test_embed_rejects_a_transcript_with_no_content(client, monkeypatch):
    monkeypatch.setattr(
        app_module, "get_transcript", lambda ticker, quarter, fiscal_year: TRANSCRIPT | {"content": None}
    )

    response = client.post(
        "/transcripts/embed", json={"ticker": "MSFT", "quarter": 3, "fiscal_year": 2024}
    )

    assert response.status_code == 422


def test_embed_returns_a_bad_gateway_when_the_cohere_call_fails(client, monkeypatch):
    def failing_embed(transcript):
        raise ApiError(status_code=429, body="rate limited")

    monkeypatch.setattr(app_module, "embed_transcript", failing_embed)

    response = client.post(
        "/transcripts/embed", json={"ticker": "MSFT", "quarter": 3, "fiscal_year": 2024}
    )

    assert response.status_code == 502
