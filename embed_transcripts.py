"""Chunk and embed transcripts already loaded in the DB, storing vectors in transcript_chunks."""
import logging

import cohere_service
import db_service

logger = logging.getLogger(__name__)


def embed_all() -> None:
    transcripts = db_service.get_all_transcripts()
    logger.info("Found %d transcripts in DB", len(transcripts))

    embedded = 0
    skipped = 0
    for transcript in transcripts:
        ticker = transcript["ticker"]
        label = f"{ticker} Q{transcript['quarter']} FY{transcript['fiscal_year']}"

        if not transcript["content"]:
            logger.warning("Skipping %s: no content", label)
            skipped += 1
            continue

        chunks = cohere_service.chunk_text(transcript["content"])
        embeddings = cohere_service.embed(chunks)
        db_service.upsert_transcript_chunks(transcript["id"], chunks, embeddings)
        logger.info("Embedded %s (%d chunks)", label, len(chunks))
        embedded += 1

    logger.info("Done: %d embedded, %d skipped", embedded, skipped)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    embed_all()
