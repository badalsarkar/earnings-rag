"""Answer a natural-language question, grounded in retrieved transcript chunks."""
import logging

from ..embeddings import chat as generate
from ..retrieval import DEFAULT_TOP_K, retrieve

logger = logging.getLogger(__name__)


def answer(query: str, top_k: int = DEFAULT_TOP_K) -> dict:
    """Retrieve the `top_k` chunks most relevant to `query` and answer grounded in them."""
    chunks = retrieve(query, top_k=top_k)
    documents = [_to_document(chunk) for chunk in chunks] or None
    logger.info(
        "Answering chat query (len=%d) with %d supporting chunks", len(query), len(chunks)
    )
    generated = generate(query, documents=documents)
    return {"answer": generated["text"], "citations": generated["citations"], "chunks": chunks}


def _to_document(chunk: dict) -> dict:
    return {
        "id": f"chunk-{chunk['id']}",
        "data": {
            "content": chunk["content"],
            "ticker": chunk["ticker"],
            "quarter": str(chunk["quarter"]),
            "fiscal_year": str(chunk["fiscal_year"]),
        },
    }
