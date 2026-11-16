"""Offline checks: chunking, quiz scoring, flashcards, and mind-map layout. No API calls."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sonar_mind.flashcards import advance_flashcard, generate_flashcards, mark_card_known, toggle_flashcard_answer
from sonar_mind.json_tools import as_item_list, parse_model_json
from sonar_mind.mindmap import calculate_safe_positioning, generate_mindmap_html
from sonar_mind.quiz import advance_to_next_question, generate_quiz_and_buttons, select_answer
from sonar_mind.rag import chunk_transcript
from sonar_mind.state import clear_transcript_data, full_transcript
from sonar_mind.transcription import load_pasted_transcript


def test_json_cleanup():
    payload = parse_model_json('```json\n[{"question": "Q", "answer": "A"}]\n```')
    items = as_item_list(payload)
    assert items[0]["question"] == "Q"


def test_chunking_and_paste():
    lecture = Path("sample_data/sample_lecture.txt").read_text(encoding="utf-8")
    shown, status = load_pasted_transcript(lecture)
    assert "relational" in shown.lower()
    assert "loaded" in status.lower()
    chunks = chunk_transcript(shown, chunk_size=400, overlap_size=50)
    assert len(chunks) >= 2
    assert chunks[0].page_content
    clear_transcript_data()
    assert full_transcript == []


def test_quiz_flow_without_model():
    import sonar_mind.state as state

    state.quiz_state = {
        "questions": [
            {"question": "What stores one record?", "options": ["Row", "Index", "Query", "Backup"], "answer": "Row"},
            {"question": "What connects two tables?", "options": ["Font", "Foreign key", "Pixel", "Theme"], "answer": "Foreign key"},
        ],
        "current_index": 0,
        "score": 0,
        "streak": 0,
        "answered": False,
    }
    question, *_rest, feedback, score = select_answer(0)
    assert "record" in question
    assert feedback == "Correct."
    assert "Score: 1" in score
    blocked = select_answer(1)
    assert "already answered" in blocked[5].lower()
    nxt = advance_to_next_question()
    assert "Foreign key" in nxt[1] or "connects" in nxt[0]
    select_answer(0)
    done = advance_to_next_question()
    assert "Quiz complete" in done[0]
    assert state.quiz_state is None


def test_flashcard_flow_without_model():
    import sonar_mind.state as state

    state.flashcard_state = {
        "cards": [{"question": "Define a primary key", "answer": "A unique row id"}],
        "current_index": 0,
        "known_cards": set(),
        "unknown_cards": set(),
        "show_answer": False,
    }
    shown = toggle_flashcard_answer()
    assert shown[1] == "A unique row id"
    summary = mark_card_known()
    assert "complete" in summary[0].lower()
    assert state.flashcard_state["known_cards"] == {0}


def test_mindmap_layout_has_no_script():
    radius, height = calculate_safe_positioning(6)
    assert radius >= 200
    assert height >= 700
    html_map = generate_mindmap_html(
        {
            "central_topic": "Databases <script>",
            "branches": [
                {"title": "Keys", "description": "Primary and foreign keys"},
                {"title": "SQL", "description": "Select, join, and filter"},
            ],
        }
    )
    assert "<script>" not in html_map
    assert "Databases" in html_map
    assert "Keys" in html_map


def test_generate_quiz_rejects_empty():
    result = generate_quiz_and_buttons("   ")
    assert "transcript" in result[0].lower()


def test_flashcards_reject_empty():
    result = generate_flashcards("")
    assert "transcript" in result[0].lower()


if __name__ == "__main__":
    test_json_cleanup()
    test_chunking_and_paste()
    test_quiz_flow_without_model()
    test_flashcard_flow_without_model()
    test_mindmap_layout_has_no_script()
    test_generate_quiz_rejects_empty()
    test_flashcards_reject_empty()
    advance_flashcard  # imported for the session helper path
    print("offline checks passed")
