"""Multiple-choice quiz generation and scoring."""

from sonar_mind.json_tools import as_item_list
from sonar_mind.llm import generate_json
from sonar_mind import state

QUIZ_TEMPLATE = """You are an educational assistant. Generate 5 multiple-choice questions based only on the transcript.
Questions should require the student to understand the lecture, not copy a single obvious word.
Return valid JSON only. No markdown. The JSON must be a list of 5 objects:
{{
  "question": "Question text",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "answer": "The correct option, copied exactly from options"
}}
Transcript:
{transcript}
JSON Output:
"""

EMPTY_BUTTONS = ("N/A", "N/A", "N/A", "N/A")


def _buttons(options) -> list[str]:
    labels = list(EMPTY_BUTTONS)
    if isinstance(options, list):
        for index, option in enumerate(options[:4]):
            labels[index] = str(option)
    return labels


def _score_line() -> str:
    if not state.quiz_state:
        return "Score: 0 | Streak: 0"
    return f"Score: {state.quiz_state.get('score', 0)} | Streak: {state.quiz_state.get('streak', 0)}"


def _pack(question, options, feedback):
    labels = _buttons(options)
    return (question, labels[0], labels[1], labels[2], labels[3], feedback, _score_line())


def generate_quiz(transcript: str):
    if not transcript or not transcript.strip():
        return "Please provide a transcript.", [], "No quiz generated."
    try:
        raw = generate_json(QUIZ_TEMPLATE, transcript)
        quiz_data = as_item_list(raw)
    except Exception as exc:
        return f"Quiz generation failed: {exc}", [], "Error occurred."
    validated = []
    for item in quiz_data:
        options = item.get("options") or []
        answer = item.get("answer")
        question = item.get("question")
        if question and isinstance(options, list) and len(options) >= 2 and answer in options:
            validated.append({"question": str(question), "options": [str(o) for o in options[:4]], "answer": str(answer)})
    if len(validated) < 1:
        return "No usable quiz questions were returned.", [], ""
    state.quiz_state = {
        "questions": validated[:5],
        "current_index": 0,
        "score": 0,
        "streak": 0,
        "answered": False,
    }
    first = state.quiz_state["questions"][0]
    return first["question"], first["options"], ""


def generate_quiz_and_buttons(transcript: str):
    question, options, feedback = generate_quiz(transcript)
    return _pack(question, options if isinstance(options, list) else [], feedback)


def select_answer(index: int):
    quiz = state.quiz_state
    if not quiz or "questions" not in quiz:
        return _pack("No quiz generated. Generate a quiz first.", EMPTY_BUTTONS, "Generate a quiz first.")
    current = quiz["questions"][quiz["current_index"]]
    options = current.get("options", [])
    if quiz.get("answered"):
        return _pack(current["question"], options, "You already answered. Click Next Question.")
    if index >= len(options):
        return _pack(current["question"], options, "That option is not available.")
    selected = options[index]
    if selected == current["answer"]:
        feedback = "Correct."
        quiz["score"] += 1
        quiz["streak"] += 1
    else:
        feedback = f"Incorrect. The correct answer was: {current['answer']}."
        quiz["streak"] = 0
    quiz["answered"] = True
    return _pack(current["question"], options, feedback)


def select_answer_and_update(index: int):
    return select_answer(index)


def advance_to_next_question():
    quiz = state.quiz_state
    if not quiz or "questions" not in quiz:
        return _pack("No quiz generated. Generate a quiz first.", EMPTY_BUTTONS, "Generate a quiz first.")
    if not quiz.get("answered"):
        current = quiz["questions"][quiz["current_index"]]
        return _pack(current["question"], current.get("options", []), "Select an answer before continuing.")
    quiz["current_index"] += 1
    quiz["answered"] = False
    if quiz["current_index"] < len(quiz["questions"]):
        nxt = quiz["questions"][quiz["current_index"]]
        return _pack(nxt["question"], nxt.get("options", []), "")
    score = quiz["score"]
    total = len(quiz["questions"])
    percentage = round((score / total) * 100) if total else 0
    color = "#d24a4a" if percentage < 60 else "#7dce6a"
    final_msg = (
        f"Quiz complete. Your score is {score} out of {total}: "
        f"<span style='color:{color}; font-weight:bold;'>{percentage}%</span>."
    )
    state.quiz_state = None
    return (final_msg, "", "", "", "", "", "Score: 0 | Streak: 0")
