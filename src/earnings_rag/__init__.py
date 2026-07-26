"""Earnings-call transcript RAG pipeline.

Subpackages:
    transcripts/  scrape earnings transcripts from Motley Fool into data/
    db/           PostgreSQL (pgvector) persistence
    embeddings/   chunking and Cohere embedding
    ingest/       batch jobs wiring the above together
    api/          FastAPI HTTP service
"""
__version__ = "0.1.0"
