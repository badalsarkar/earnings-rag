"""HTTP behavior of the search endpoint.

Ranking is covered in test_retrieval.py; what matters here is the contract at
the edge — what a client sends, what comes back, and which inputs are rejected
before any embedding is paid for. The stubs go in at the same seam
test_retrieval.py uses, so the endpoint and `retrieve` both run for real.
"""
import pytest
from fastapi.testclient import TestClient

from earnings_rag.api import app
from earnings_rag.retrieval import retrieval

CHUNKS = [
    {
        "id": 1, "transcript_id": 10, "chunk_index": 0, "vector": [1.0, 0.0],
        "content": "Cloud revenue grew 31% year over year.",
        "ticker": "MSFT", "quarter": 3, "fiscal_year": 2024, "report_date": "2024-04-25",
    },
    {
        "id": 2, "transcript_id": 11, "chunk_index": 0, "vector": [0.0, 1.0],
        "content": "We repurchased $4.1 billion of stock.",
        "ticker": "GOOGL", "quarter": 1, "fiscal_year": 2025, "report_date": "2025-02-04",
    },
]

QUERY_VECTORS = {
    "how did cloud do": [1.0, 0.0],
    "buybacks": [0.0, 1.0],
}


@pytest.fixture
def client(monkeypatch):
    """A client backed by a stub store, so no Cohere or Postgres call is made."""

    def fake_embed_query(query: str) -> list[float]:
        return QUERY_VECTORS[query]

    def fake_search_chunks(embedding: list[float], limit: int = 5) -> list[dict]:
        ranked = sorted(
            CHUNKS,
            key=lambda c: sum(x * y for x, y in zip(embedding, c["vector"], strict=True)),
            reverse=True,
        )
        return [
            {k: v for k, v in c.items() if k != "vector"} | {"similarity": 0.9}
            for c in ranked[:limit]
        ]

    monkeypatch.setattr(retrieval, "embed_query", fake_embed_query)
    monkeypatch.setattr(retrieval, "search_chunks", fake_search_chunks)
    return TestClient(app)


def test_search_returns_the_nearest_chunk_first(client):
    response = client.post("/search", json={"query": "buybacks"})

    assert response.status_code == 200
    assert response.json()[0]["content"] == "We repurchased $4.1 billion of stock."


def test_search_results_carry_transcript_metadata(client):
    top = client.post("/search", json={"query": "how did cloud do"}).json()[0]

    assert (top["ticker"], top["quarter"], top["fiscal_year"]) == ("MSFT", 3, 2024)
    assert top["report_date"] == "2024-04-25"
    assert "similarity" in top


def test_top_k_caps_the_number_of_results(client):
    response = client.post("/search", json={"query": "buybacks", "top_k": 1})

    assert len(response.json()) == 1


def test_empty_query_returns_no_chunks(client):
    response = client.post("/search", json={"query": ""})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("top_k", [0, -1, 51])
def test_out_of_range_top_k_is_rejected(client, top_k):
    assert client.post("/search", json={"query": "buybacks", "top_k": top_k}).status_code == 422


def test_missing_query_is_rejected(client):
    assert client.post("/search", json={}).status_code == 422
