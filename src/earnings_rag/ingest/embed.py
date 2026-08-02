"""Chunk and embed transcripts already in the DB, storing vectors in transcript_chunks."""
import logging

from cohere.core.api_error import ApiError

from ..config import configure_logging, load_env
from ..db import get_all_transcripts, upsert_transcript_chunks
from ..embeddings import chunk_text, embed

logger = logging.getLogger(__name__)


def embed_transcript(transcript: dict) -> int:
    """Chunk and embed one transcript row, upserting its chunks. Returns the chunk count."""
    chunks = chunk_text(transcript["content"])
    embeddings = embed(chunks)
    upsert_transcript_chunks(transcript["id"], chunks, embeddings)
    return len(chunks)


def embed_all() -> None:
    transcripts = get_all_transcripts()
    logger.info("Found %d transcripts in DB", len(transcripts))

    embedded = skipped = errored = 0
    for transcript in transcripts:
        label = (
            f"{transcript['ticker']} Q{transcript['quarter']} FY{transcript['fiscal_year']}"
        )

        if not transcript["content"]:
            logger.warning("Skipping %s: no content", label)
            skipped += 1
            continue

        try:
            chunk_count = embed_transcript(transcript)
        except ApiError:
            # embed() is all-or-nothing, so no chunks were written for this
            # transcript; drop it and move on rather than retrying.
            logger.exception("Dropping %s: embedding call failed", label)
            errored += 1
            continue

        logger.info("Embedded %s (%d chunks)", label, chunk_count)
        embedded += 1

    logger.info("Done: %d embedded, %d skipped, %d errored", embedded, skipped, errored)


def main() -> None:
    load_env()
    configure_logging()
    embed_all()


if __name__ == "__main__":
    main()
