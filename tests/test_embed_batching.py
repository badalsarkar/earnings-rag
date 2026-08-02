"""Batching behavior of the embed() wrapper around Cohere's embed endpoint.

Cohere's embed endpoint caps requests at 96 texts, so embed() must split
larger inputs into multiple calls and stitch the results back together in
order, while staying atomic: a failed call must not yield partial results.
"""
import pytest
from cohere.core.api_error import ApiError

from earnings_rag.embeddings import cohere_client


@pytest.fixture
def fake_embed(monkeypatch):
    calls = []

    def _fake_embed(texts, input_type):
        calls.append(list(texts))
        return [[float(i)] for i in range(len(texts))]

    monkeypatch.setattr(cohere_client, "_embed", _fake_embed)
    return calls


def test_embed_batches_at_the_96_text_cap(fake_embed):
    texts = [f"chunk {i}" for i in range(200)]

    cohere_client.embed(texts)

    assert [len(batch) for batch in fake_embed] == [96, 96, 8]


def test_embed_stitches_batches_back_together_in_order(fake_embed):
    texts = [f"chunk {i}" for i in range(150)]

    embeddings = cohere_client.embed(texts)

    assert len(embeddings) == 150


def test_embed_under_the_cap_makes_a_single_call(fake_embed):
    cohere_client.embed(["one", "two"])

    assert len(fake_embed) == 1


def test_a_failed_batch_raises_without_returning_partial_results(monkeypatch):
    def flaky_embed(texts, input_type):
        if len(texts) < 96:
            raise ApiError(status_code=429, body="rate limited")
        return [[0.0] for _ in texts]

    monkeypatch.setattr(cohere_client, "_embed", flaky_embed)

    with pytest.raises(ApiError):
        cohere_client.embed([f"chunk {i}" for i in range(150)])
