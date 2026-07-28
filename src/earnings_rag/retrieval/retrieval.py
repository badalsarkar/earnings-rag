"""Turn a natural-language query into the transcript chunks most like it."""
import logging

from ..db import search_chunks
from ..embeddings import embed_query

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """Embed `query` and return the `top_k` nearest chunks, closest first.

    The query is embedded with input_type="search_query" while stored chunks use
    "search_document" — the asymmetry is required by Cohere's v3 embed models.
    """
    if not query:
        logger.debug("Empty query, skipping retrieval")
        return []

    logger.info("Retrieving top %d chunks for query (len=%d)", top_k, len(query))
    logger.debug("Query text: %r", query)
    query_vector = embed_query(query)
    return search_chunks(query_vector, limit=top_k)

