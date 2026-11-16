"""Flashcards for active recall."""

from sonar_mind.json_tools import as_item_list
from sonar_mind.llm import generate_json
from sonar_mind import state

FLASHCARD_TEMPLATE = """You are an educational assistant. Generate 5 flashcards from the transcript only.
Cover definitions, key facts, and main ideas. Return valid JSON only, a list of 5 objects:
{{
  "question": "A specific question",
  "answer": "A concise answer from the lecture"
}}
Transcript:
{transcript}
JSON Output:
"""


def _view(question: str, answer: str, status: str, button: str):
    cards = (state.flashcard_state or {}).get("cards") or []
    index = (state.flashcard_state or {}).get("current_index", 0)
    progress = f"{min(index + 1, len(cards))}/{len(cards)}" if cards else "0/0"
    return question, answer, status, progress, button


def generate_flashcards(transcript: str):
    if not transcript or not transcript.strip():
        return _view("Please provide a transcript.", "", "No flashcards generated.", "Show Answer")
    try:
        raw = generate_json(FLASHCARD_TEMPLATE, transcript)
        cards = []
        for item in as_item_list(raw):
            if item.get("question") and item.get("answer"):
                cards.append({"question": str(item["question"]), "answer": str(item["answer"])})
        if not cards:
            raise ValueError("No flashcards returned by the model.")
    except Exception as exc:
        return _view(f"Flashcard generation failed: {exc}", "", "Error occurred.", "Show Answer")
    state.flashcard_state = {
        "cards": cards[:5],
        "current_index": 0,
        "known_cards": set(),
        "unknown_cards": set(),
        "show_answer": False,
    }
    return _view(
        cards[0]["question"],
        "",
        "Flashcards ready. Click Show Answer when you have tried to recall it.",
        "Show Answer",
    )


def toggle_flashcard_answer():
    deck = state.flashcard_state
    if not deck or "cards" not in deck:
        return _view("No flashcards generated.", "", "Generate flashcards first.", "Show Answer")
    card = deck["cards"][deck["current_index"]]
    deck["show_answer"] = not deck["show_answer"]
    if deck["show_answer"]:
        return _view(card["question"], card["answer"], "Mark this card as known or still to review.", "Hide Answer")
    return _view(card["question"], "", "Answer hidden.", "Show Answer")


def advance_flashcard():
    deck = state.flashcard_state
    if not deck or "cards" not in deck:
        return _view("No flashcards generated.", "", "Generate flashcards first.", "Show Answer")
    deck["current_index"] += 1
    deck["show_answer"] = False
    if deck["current_index"] >= len(deck["cards"]):
        known = len(deck["known_cards"])
        unknown = len(deck["unknown_cards"])
        total = len(deck["cards"])
        mastery = (known / total) * 100 if total else 0
        summary = (
            f"Flashcard session complete. Total {total}. Known {known}. "
            f"Still reviewing {unknown}. Mastery {mastery:.0f}%."
        )
        return summary, "", "Generate a new set to study again.", f"{total}/{total}", "Show Answer"
    card = deck["cards"][deck["current_index"]]
    return _view(card["question"], "", "New card. Recall the answer, then reveal it.", "Show Answer")


def mark_card_known():
    deck = state.flashcard_state
    if not deck or "cards" not in deck:
        return _view("No flashcards generated.", "", "Generate flashcards first.", "Show Answer")
    deck["known_cards"].add(deck["current_index"])
    deck["unknown_cards"].discard(deck["current_index"])
    return advance_flashcard()


def mark_card_unknown():
    deck = state.flashcard_state
    if not deck or "cards" not in deck:
        return _view("No flashcards generated.", "", "Generate flashcards first.", "Show Answer")
    deck["unknown_cards"].add(deck["current_index"])
    deck["known_cards"].discard(deck["current_index"])
    return advance_flashcard()


def previous_flashcard():
    deck = state.flashcard_state
    if not deck or "cards" not in deck:
        return _view("No flashcards generated.", "", "Generate flashcards first.", "Show Answer")
    if deck["current_index"] == 0:
        card = deck["cards"][0]
        answer = card["answer"] if deck["show_answer"] else ""
        button = "Hide Answer" if deck["show_answer"] else "Show Answer"
        return _view(card["question"], answer, "Already at the first card.", button)
    deck["current_index"] -= 1
    deck["show_answer"] = False
    card = deck["cards"][deck["current_index"]]
    return _view(card["question"], "", "Previous card.", "Show Answer")
