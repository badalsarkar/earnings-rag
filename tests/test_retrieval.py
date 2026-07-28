"""Retrieval behavior.

Ranking is done by pgvector, not by our Python, so the ordering guarantee is
verified against a real database in the integration tests at the bottom of this
file. The fast tests cover what `retrieve` itself does: skip empty queries,
embed the query, and hand back the ranked chunks the store returned.
"""
import math

import psycopg
import pytest

from earnings_rag.config import postgres_dsn
from earnings_rag.db import connection, search_chunks, upsert_transcript, upsert_transcript_chunks
from earnings_rag.retrieval import retrieval

# Three chunks pointing along different axes, so "nearest" is obvious by eye.
CORPUS = [
    {
        "id": 1, "transcript_id": 10, "chunk_index": 0, "vector": [1.0, 0.0, 0.0],
        "content": "Cloud revenue grew 31% year over year.",
        "ticker": "MSFT", "quarter": 3, "fiscal_year": 2024,
    },
    {
        "id": 2, "transcript_id": 10, "chunk_index": 1, "vector": [0.0, 1.0, 0.0],
        "content": "Headcount was roughly flat this quarter.",
        "ticker": "MSFT", "quarter": 3, "fiscal_year": 2024,
    },
    {
        "id": 3, "transcript_id": 11, "chunk_index": 0, "vector": [0.0, 0.0, 1.0],
        "content": "We repurchased $4.1 billion of stock.",
        "ticker": "GOOGL", "quarter": 1, "fiscal_year": 2025,
    },
]

# What the stub embedder returns for each query phrase.
QUERY_VECTORS = {
    "how did cloud do": [0.9, 0.1, 0.0],
    "did they hire": [0.1, 0.9, 0.0],
    "buybacks": [0.0, 0.1, 0.9],
}


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    return dot / (math.hypot(*a) * math.hypot(*b))


@pytest.fixture
def store(monkeypatch):
    """Stand in for pgvector: embed known phrases, return chunks nearest first.

    This replaces the database, not the code under test — `retrieve` still does
    its own work on top of whatever the store hands back.
    """

    def fake_embed_query(query: str) -> list[float]:
        return QUERY_VECTORS[query]

    def fake_search_chunks(embedding: list[float], limit: int = 5) -> list[dict]:
        ranked = sorted(
            CORPUS, key=lambda c: cosine_similarity(embedding, c["vector"]), reverse=True
        )
        return [
            {k: v for k, v in chunk.items() if k != "vector"}
            | {"similarity": cosine_similarity(embedding, chunk["vector"])}
            for chunk in ranked[:limit]
        ]

    monkeypatch.setattr(retrieval, "embed_query", fake_embed_query)
    monkeypatch.setattr(retrieval, "search_chunks", fake_search_chunks)


def test_empty_query_retrieves_nothing():
    assert retrieval.retrieve("") == []


@pytest.mark.parametrize(
    ("query", "expected_content"),
    [
        ("how did cloud do", "Cloud revenue grew 31% year over year."),
        ("did they hire", "Headcount was roughly flat this quarter."),
        ("buybacks", "We repurchased $4.1 billion of stock."),
    ],
)
def test_most_similar_chunk_ranks_first(store, query, expected_content):
    results = retrieval.retrieve(query)

    assert results[0]["content"] == expected_content


def test_results_are_ordered_by_descending_similarity(store):
    results = retrieval.retrieve("how did cloud do")

    similarities = [row["similarity"] for row in results]
    assert similarities == sorted(similarities, reverse=True)


def test_top_k_caps_the_number_of_chunks(store):
    assert len(retrieval.retrieve("how did cloud do", top_k=2)) == 2


def test_retrieved_chunks_carry_their_transcript_metadata(store):
    top = retrieval.retrieve("buybacks")[0]

    assert (top["ticker"], top["quarter"], top["fiscal_year"]) == ("GOOGL", 1, 2025)


# --- Integration: the ordering guarantee, against a real pgvector index --------

EMBEDDING_DIM = 1024
TEST_TICKER = "ZZTEST"


def basis_vector(axis: int) -> list[float]:
    """A 1024-d unit vector along one axis, matching the column's dimension."""
    vector = [0.0] * EMBEDDING_DIM
    vector[axis] = 1.0
    return vector


def postgres_is_reachable() -> bool:
    try:
        with psycopg.connect(postgres_dsn(), connect_timeout=2):
            return True
    except psycopg.Error:
        return False


requires_postgres = pytest.mark.skipif(
    not postgres_is_reachable(), reason="PostgreSQL not reachable; run `docker compose up -d`"
)


@pytest.fixture
def seeded_transcript():
    """Insert a transcript with three orthogonal chunk vectors, then remove it."""
    from datetime import date

    transcript = upsert_transcript(
        ticker=TEST_TICKER,
        quarter=1,
        fiscal_year=2099,
        report_date=date(2099, 1, 15),
        content="fixture transcript",
    )
    upsert_transcript_chunks(
        transcript_id=transcript["id"],
        chunks=["axis zero chunk", "axis one chunk", "axis two chunk"],
        embeddings=[basis_vector(0), basis_vector(1), basis_vector(2)],
    )
    yield transcript
    with connection() as conn:
        conn.execute("DELETE FROM transcripts WHERE ticker = %s", (TEST_TICKER,))


@pytest.mark.integration
@requires_postgres
def test_pgvector_ranks_the_nearest_chunk_first(seeded_transcript):
    results = search_chunks(basis_vector(1), limit=3)

    ours = [row for row in results if row["ticker"] == TEST_TICKER]
    assert ours[0]["content"] == "axis one chunk"
    assert ours[0]["similarity"] == pytest.approx(1.0, abs=1e-6)


@pytest.mark.integration
@requires_postgres
def test_pgvector_respects_the_limit(seeded_transcript):
    assert len(search_chunks(basis_vector(0), limit=2)) == 2
