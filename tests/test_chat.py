"""Chat behavior: turning a question into a grounded answer.

Retrieval ranking is covered in test_retrieval.py and generation itself is a
Cohere API call, so both are stubbed here. What matters in this module is the
glue: retrieved chunks become the model's supporting documents, and whatever
the model returns is handed back alongside the chunks it was grounded in.
"""
import pytest

from earnings_rag.chat import chat

CHUNKS = [
    {
        "id": 1, "transcript_id": 10, "chunk_index": 0,
        "content": "Cloud revenue grew 31% year over year.",
        "similarity": 0.91,
        "ticker": "MSFT", "quarter": 3, "fiscal_year": 2024, "report_date": "2024-04-25",
    },
    {
        "id": 2, "transcript_id": 11, "chunk_index": 0,
        "content": "We repurchased $4.1 billion of stock.",
        "similarity": 0.85,
        "ticker": "GOOGL", "quarter": 1, "fiscal_year": 2025, "report_date": "2025-02-04",
    },
]

GENERATED = {
    "text": "Cloud revenue was up 31% year over year.",
    "citations": [
        {"start": 0, "end": 17, "text": "Cloud revenue was", "sources": ["chunk-1"]},
    ],
}


@pytest.fixture
def stubs(monkeypatch):
    """Stand in for retrieval and the Cohere chat call."""
    calls = {}

    def fake_retrieve(query, top_k):
        calls["retrieve"] = (query, top_k)
        return CHUNKS

    def fake_generate(query, documents=None):
        calls["generate"] = (query, documents)
        return GENERATED

    monkeypatch.setattr(chat, "retrieve", fake_retrieve)
    monkeypatch.setattr(chat, "generate", fake_generate)
    return calls


def test_answer_returns_generated_text(stubs):
    result = chat.answer("how did cloud do")

    assert result["answer"] == GENERATED["text"]


def test_answer_returns_citations(stubs):
    result = chat.answer("how did cloud do")

    assert result["citations"] == GENERATED["citations"]


def test_answer_returns_the_supporting_chunks(stubs):
    result = chat.answer("how did cloud do")

    assert result["chunks"] == CHUNKS


def test_answer_forwards_top_k_to_retrieve(stubs):
    chat.answer("how did cloud do", top_k=2)

    assert stubs["retrieve"] == ("how did cloud do", 2)


def test_answer_passes_retrieved_chunks_as_documents(stubs):
    chat.answer("how did cloud do")

    _, documents = stubs["generate"]
    assert [d["data"]["content"] for d in documents] == [c["content"] for c in CHUNKS]


def test_answer_document_ids_are_traceable_to_their_chunk(stubs):
    chat.answer("how did cloud do")

    _, documents = stubs["generate"]
    assert documents[0]["id"] == "chunk-1"
    assert documents[1]["id"] == "chunk-2"


def test_answer_with_no_matching_chunks_generates_without_documents(monkeypatch):
    calls = {}

    def fake_generate(query, documents=None):
        calls["documents"] = documents
        return GENERATED

    monkeypatch.setattr(chat, "retrieve", lambda query, top_k: [])
    monkeypatch.setattr(chat, "generate", fake_generate)

    result = chat.answer("anything")

    assert calls["documents"] is None
    assert result["chunks"] == []
