"""Query embedding and nearest-chunk retrieval."""
from .retrieval import DEFAULT_TOP_K, retrieve

__all__ = [
    "DEFAULT_TOP_K",
    "retrieve",
]
