"""Cohere client: chat, embeddings, and the tokenizer used for chunking."""
import logging
from functools import lru_cache

import cohere
import requests
from cohere.core.api_error import ApiError
from tokenizers import Tokenizer

from .chunking import CHUNK_OVERLAP, CHUNK_SIZE, chunk_tokens

logger = logging.getLogger(__name__)

CHAT_MODEL = "command-r-plus-08-2024"
EMBED_MODEL = "embed-english-v3.0"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Chunk text on the embedding model's own tokenizer."""
    return chunk_tokens(text, _get_tokenizer(), chunk_size, overlap)


def embed(texts: list[str]) -> list[list[float]]:
    return _embed(texts, "search_document")


def embed_query(query: str) -> list[float]:
    return _embed([query], "search_query")[0]


def chat(query: str) -> str:
    message = [{"role": "user", "content": query}]
    # https://docs.cohere.com/reference/chat
    logger.info("Cohere chat call: model=%s query_len=%d", CHAT_MODEL, len(query))
    try:
        response = _get_client().chat(model=CHAT_MODEL, messages=message)
    except ApiError:
        logger.exception("Cohere chat call failed: model=%s", CHAT_MODEL)
        raise
    return response.message.content[0].text


def _embed(texts: list[str], input_type: str) -> list[list[float]]:
    # https://docs.cohere.com/reference/embed
    logger.info(
        "Cohere embed call: model=%s input_type=%s texts=%d", EMBED_MODEL, input_type, len(texts)
    )
    try:
        embeddings = _get_client().embed(
            model=EMBED_MODEL,
            texts=texts,
            input_type=input_type,
            embedding_types=["float"],
        ).embeddings.float
    except ApiError:
        logger.exception(
            "Cohere embed call failed: model=%s input_type=%s texts=%d",
            EMBED_MODEL, input_type, len(texts),
        )
        raise
    logger.info("Cohere embed call succeeded: %d embeddings returned", len(embeddings))
    return embeddings


@lru_cache(maxsize=1)
def _get_tokenizer() -> Tokenizer:
    # https://docs.cohere.com/reference/get-model
    logger.info("Cohere models.get call: model=%s", EMBED_MODEL)
    try:
        model_info = _get_client().models.get(EMBED_MODEL)
    except ApiError:
        logger.exception("Cohere models.get call failed: model=%s", EMBED_MODEL)
        raise
    tokenizer_json = requests.get(model_info.tokenizer_url, timeout=10).text
    # https://huggingface.co/docs/tokenizers/api/tokenizer#tokenizers.Tokenizer.from_str
    return Tokenizer.from_str(tokenizer_json)


@lru_cache(maxsize=1)
def _get_client() -> cohere.ClientV2:
    return cohere.ClientV2()
