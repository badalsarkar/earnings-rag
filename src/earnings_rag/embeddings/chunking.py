"""Token-window chunking.

Kept free of any Cohere import so the windowing logic can be tested with any
tokenizer; ``cohere.chunk_text`` supplies the real one.
"""
from typing import Protocol


class Tokenizer(Protocol):
    """The slice of the HuggingFace ``Tokenizer`` API used here."""

    def encode(self, text: str): ...

    def decode(self, ids: list[int]) -> str: ...


CHUNK_SIZE = 400
CHUNK_OVERLAP = 50


def chunk_tokens(
    text: str,
    tokenizer: Tokenizer,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping windows of ``chunk_size`` tokens.

    Empty chunks are dropped, so the result may be shorter than the token count
    implies.
    """
    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")

    token_ids = tokenizer.encode(text).ids
    chunks = []
    start = 0
    while start < len(token_ids):
        end = min(start + chunk_size, len(token_ids))
        chunks.append(tokenizer.decode(token_ids[start:end]).strip())
        start += chunk_size - overlap
    return [c for c in chunks if c]
