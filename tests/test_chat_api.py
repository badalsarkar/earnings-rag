"""HTTP behavior of the chat endpoint.

The glue between retrieval and generation is covered in test_chat.py; what
matters here is the contract at the edge, stubbed at the same seam so the
endpoint and `chat.answer` both run for real.
"""
import pytest
from fastapi.testclient import TestClient

from earnings_rag.api import app
from earnings_rag.chat import chat

CHUNKS = [
    {
        "id": 1, "transcript_id": 10, "chunk_index": 0,
        "content": "Cloud revenue grew 31% year over year.",
        "similarity": 0.91,
        "ticker": "MSFT", "quarter": 3, "fiscal_year": 2024, "report_date": "2024-04-25",
    },
]

GENERATED = {
    "text": "Cloud revenue was up 31% year over year.",
    "citations": [
        {"start": 0, "end": 17, "text": "Cloud revenue was", "sources": ["chunk-1"]},
    ],
}


@pytest.fixture
def client(monkeypatch):
    """A client backed by stub retrieval and generation, so no Cohere or Postgres call is made."""
    monkeypatch.setattr(chat, "retrieve", lambda query, top_k: CHUNKS)
    monkeypatch.setattr(chat, "generate", lambda query, documents=None: GENERATED)
    return TestClient(app)


def test_chat_returns_the_generated_answer(client):
    response = client.post("/chat", json={"query": "how did cloud do"})

    assert response.status_code == 200
    assert response.json()["answer"] == GENERATED["text"]


def test_chat_returns_citations(client):
    response = client.post("/chat", json={"query": "how did cloud do"})

    assert response.json()["citations"] == GENERATED["citations"]


def test_chat_returns_the_supporting_chunks(client):
    response = client.post("/chat", json={"query": "how did cloud do"})

    top = response.json()["chunks"][0]
    assert (top["ticker"], top["quarter"], top["fiscal_year"]) == ("MSFT", 3, 2024)
    assert top["content"] == "Cloud revenue grew 31% year over year."


def test_empty_query_is_rejected(client):
    assert client.post("/chat", json={"query": ""}).status_code == 422


def test_missing_query_is_rejected(client):
    assert client.post("/chat", json={}).status_code == 422


@pytest.mark.parametrize("top_k", [0, -1, 51])
def test_out_of_range_top_k_is_rejected(client, top_k):
    response = client.post("/chat", json={"query": "how did cloud do", "top_k": top_k})
    assert response.status_code == 422
