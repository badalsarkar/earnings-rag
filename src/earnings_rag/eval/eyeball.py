"""Interactive eyeball eval: ask a question, show the grounded answer, record an opinion.

Each round is appended as one record to `eval_runs/eyball.json` — the raw material
for later reviewing how well retrieval + generation are doing, question by question.
"""
import json
from pathlib import Path

from ..chat import answer
from ..config import EVAL_RUNS_DIR, configure_logging, load_env
from ..retrieval import DEFAULT_TOP_K

EYBALL_JSON_PATH = EVAL_RUNS_DIR / "eyball.json"


def top_chunk_ids(chunks: list[dict]) -> list[int]:
    return [chunk["id"] for chunk in chunks]


def record_round(json_path: Path, question: str, result: dict, opinion: str) -> None:
    """Append one eval record, creating the JSON array if the file is new or empty."""
    if json_path.exists() and json_path.stat().st_size > 0:
        records = json.loads(json_path.read_text())
    else:
        records = []

    records.append(
        {
            "question": question,
            "answer": result["answer"],
            "top_chunk_ids": top_chunk_ids(result["chunks"]),
            "one_line_opinion": opinion,
        }
    )
    json_path.write_text(json.dumps(records, indent=2) + "\n")


def repl(json_path: Path = EYBALL_JSON_PATH, top_k: int = DEFAULT_TOP_K) -> None:
    """Ask a question, print the grounded answer, record an opinion. Blank question quits."""
    while True:
        question = input("Question (blank to quit): ").strip()
        if not question:
            break

        result = answer(question, top_k)
        print(f"\nAnswer: {result['answer']}")
        print(f"Top chunks: {top_chunk_ids(result['chunks'])}\n")

        opinion = input("One-line opinion: ").strip()
        record_round(json_path, question, result, opinion)


def main() -> None:
    load_env()
    configure_logging()
    EVAL_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    repl()


if __name__ == "__main__":
    main()
