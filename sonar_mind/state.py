"""Shared session state used by transcription, retrieval, quizzes, and study tools."""

full_transcript: list[str] = []
vector_db = None
rag_chain = None
quiz_state = None
flashcard_state = None
mindmap_state = None


def get_full_transcript_text() -> str:
    return " ".join(part.strip() for part in full_transcript if part and part.strip())


def clear_transcript_data() -> str:
    """Reset lecture memory so a new recording does not mix with the previous one."""
    global vector_db, rag_chain, quiz_state, flashcard_state, mindmap_state
    full_transcript.clear()
    vector_db = None
    rag_chain = None
    quiz_state = None
    flashcard_state = None
    mindmap_state = None
    print("Transcript data cleared.")
    return ""
