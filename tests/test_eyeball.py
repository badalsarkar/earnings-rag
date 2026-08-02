"""Interactive eyeball-eval loop: ask a question, show the answer, record an opinion.

Generation is a Cohere call and is stubbed here; what matters is the glue —
each round becomes one JSON record with the question, answer, retrieved chunk
ids, and the human's one-line opinion.
"""
import json

import pytest

from earnings_rag.eval import eyeball

CHUNKS = [
    {
        "id": 1, "transcript_id": 10, "chunk_index": 0,
        "content": "Cloud revenue grew 31% year over year.",
        "similarity": 0.91,
        "ticker": "MSFT", "quarter": 3, "fiscal_year": 2024, "report_date": "2024-04-25",
    },
    {
        "id": 2, "transcript_id": 11, "chunk_index": 0,
        "content": "We repurchased $4.1 billion of stock.",
        "similarity": 0.85,
        "ticker": "GOOGL", "quarter": 1, "fiscal_year": 2025, "report_date": "2025-02-04",
    },
]

RESULT = {
    "answer": "Cloud revenue was up 31% year over year.",
    "citations": [
        {"start": 0, "end": 17, "text": "Cloud revenue was", "sources": ["chunk-1"]},
    ],
    "chunks": CHUNKS,
}


def test_top_chunk_ids_lists_ids_in_order():
    assert eyeball.top_chunk_ids(CHUNKS) == [1, 2]


def test_top_chunk_ids_empty_for_no_chunks():
    assert eyeball.top_chunk_ids([]) == []


def test_record_round_writes_a_json_array_to_new_file(tmp_path):
    json_path = tmp_path / "eyball.json"

    eyeball.record_round(json_path, "how did cloud do", RESULT, "accurate and concise")

    records = json.loads(json_path.read_text())
    assert records == [
        {
            "question": "how did cloud do",
            "answer": RESULT["answer"],
            "top_chunk_ids": [1, 2],
            "one_line_opinion": "accurate and concise",
        }
    ]


def test_record_round_writes_to_file_that_exists_but_is_empty(tmp_path):
    json_path = tmp_path / "eyball.json"
    json_path.touch()

    eyeball.record_round(json_path, "how did cloud do", RESULT, "good")

    records = json.loads(json_path.read_text())
    assert len(records) == 1
    assert records[0]["question"] == "how did cloud do"


def test_record_round_appends_to_existing_array(tmp_path):
    json_path = tmp_path / "eyball.json"

    eyeball.record_round(json_path, "q1", RESULT, "good")
    eyeball.record_round(json_path, "q2", RESULT, "meh")

    records = json.loads(json_path.read_text())
    assert [r["question"] for r in records] == ["q1", "q2"]


@pytest.fixture
def stub_answer(monkeypatch):
    calls = {}

    def fake_answer(query, top_k):
        calls["answer"] = (query, top_k)
        return RESULT

    monkeypatch.setattr(eyeball, "answer", fake_answer)
    return calls


def test_repl_records_one_round_per_question(monkeypatch, tmp_path, stub_answer):
    json_path = tmp_path / "eyball.json"
    responses = iter(["how did cloud do", "accurate", ""])
    monkeypatch.setattr("builtins.input", lambda *_: next(responses))

    eyeball.repl(json_path)

    records = json.loads(json_path.read_text())
    assert records == [
        {
            "question": "how did cloud do",
            "answer": RESULT["answer"],
            "top_chunk_ids": [1, 2],
            "one_line_opinion": "accurate",
        }
    ]


def test_repl_stops_on_blank_question(monkeypatch, tmp_path, stub_answer):
    json_path = tmp_path / "eyball.json"
    monkeypatch.setattr("builtins.input", lambda *_: "")

    eyeball.repl(json_path)

    assert "answer" not in stub_answer
    assert not json_path.exists()


def test_repl_handles_multiple_rounds(monkeypatch, tmp_path, stub_answer):
    json_path = tmp_path / "eyball.json"
    responses = iter(["q1", "opinion1", "q2", "opinion2", ""])
    monkeypatch.setattr("builtins.input", lambda *_: next(responses))

    eyeball.repl(json_path)

    records = json.loads(json_path.read_text())
    assert [r["question"] for r in records] == ["q1", "q2"]
    assert [r["one_line_opinion"] for r in records] == ["opinion1", "opinion2"]
