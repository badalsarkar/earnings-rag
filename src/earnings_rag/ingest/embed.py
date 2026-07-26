"""Chunk and embed transcripts already in the DB, storing vectors in transcript_chunks."""
import logging

from ..config import configure_logging, load_env
from ..db import get_all_transcripts, upsert_transcript_chunks
from ..embeddings import chunk_text, embed

logger = logging.getLogger(__name__)


def embed_all() -> None:
    transcripts = get_all_transcripts()
    logger.info("Found %d transcripts in DB", len(transcripts))

    embedded = skipped = 0
    for transcript in transcripts:
        label = (
            f"{transcript['ticker']} Q{transcript['quarter']} FY{transcript['fiscal_year']}"
        )

        if not transcript["content"]:
            logger.warning("Skipping %s: no content", label)
            skipped += 1
            continue

        chunks = chunk_text(transcript["content"])
        embeddings = embed(chunks)
        upsert_transcript_chunks(transcript["id"], chunks, embeddings)
        logger.info("Embedded %s (%d chunks)", label, len(chunks))
        embedded += 1

    logger.info("Done: %d embedded, %d skipped", embedded, skipped)


def main() -> None:
    load_env()
    configure_logging()
    embed_all()


if __name__ == "__main__":
    main()
