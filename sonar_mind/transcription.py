"""Upload lecture audio to Gemini and return a plain-text transcript."""

from google import genai

from sonar_mind.config import GEMINI_MODEL, get_api_key
from sonar_mind import state
from sonar_mind.state import get_full_transcript_text

TRANSCRIBE_PROMPT = (
    "Perform speech-to-text transcription for the provided lecture audio. "
    "Write the transcript as plain paragraphs, then a short section titled Key points "
    "with a numbered list. Use only what is spoken. Do not return JSON."
)


def transcribe_audio_chunk(audio_path: str) -> str:
    if not audio_path:
        return "Error: No audio file path was provided."
    try:
        client = genai.Client(api_key=get_api_key())
        uploaded_file = client.files.upload(file=audio_path)
        print(f"File uploaded. URI: {uploaded_file.uri}, Name: {uploaded_file.name}")
        print("Sending transcription request to Gemini...")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[TRANSCRIBE_PROMPT, uploaded_file],
        )
        text = getattr(response, "text", None)
        if text and text.strip():
            print("Transcription successful.")
            return text.strip()
        if not getattr(response, "candidates", None):
            feedback = getattr(response, "prompt_feedback", None)
            reason = getattr(feedback, "block_reason", None) or "Unknown"
            return f"Transcription failed. Block reason: {reason}"
        return "Error: Failed to parse transcription response."
    except Exception as exc:
        return f"Transcription error: {exc}"


def format_transcription_result(result_text: str) -> str:
    return (result_text or "").strip()


def handle_transcription_request(audio_file):
    """Gradio callback: transcribe one upload and append it to the lecture."""
    import gradio as gr

    if audio_file is None:
        return (
            "",
            get_full_transcript_text(),
            gr.update(value=None),
            "Transcription not initiated.",
            "Input declined. No audio file provided.",
        )
    transcript_text = transcribe_audio_chunk(audio_file)
    formatted_chunk = format_transcription_result(transcript_text)
    if formatted_chunk.lower().startswith(("transcription error", "error:", "transcription failed")):
        return (
            formatted_chunk,
            get_full_transcript_text(),
            gr.update(value=None),
            "Transcription failed.",
            formatted_chunk,
        )
    state.full_transcript.append(formatted_chunk)
    return (
        formatted_chunk,
        get_full_transcript_text(),
        gr.update(value=None),
        "Transcription successful.",
        "Input accepted. Audio file processed.",
    )


def handle_clear_transcript():
    from sonar_mind.state import clear_transcript_data

    clear_transcript_data()
    return "", "Transcript cleared."


def load_pasted_transcript(pasted_text: str):
    """Let a student paste notes when they do not have an audio file."""
    from sonar_mind.state import clear_transcript_data

    text = (pasted_text or "").strip()
    if not text:
        return get_full_transcript_text(), "Paste lecture text before loading it."
    clear_transcript_data()
    state.full_transcript.append(text)
    return get_full_transcript_text(), "Pasted transcript loaded. Index it before asking questions."
