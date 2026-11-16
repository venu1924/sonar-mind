"""Gradio interface for Sonar Mind."""

import gradio as gr

from sonar_mind.flashcards import (
    advance_flashcard,
    generate_flashcards,
    mark_card_known,
    mark_card_unknown,
    previous_flashcard,
    toggle_flashcard_answer,
)
from sonar_mind.mindmap import generate_mindmap
from sonar_mind.quiz import advance_to_next_question, generate_quiz_and_buttons, select_answer_and_update
from sonar_mind.rag import handle_indexing_request, handle_query_request
from sonar_mind.transcription import handle_clear_transcript, handle_transcription_request, load_pasted_transcript

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Raleway:wght@400;500&display=swap');
body, .gradio-container, button, h1, h2, h3, p, label, textarea, input {
  font-family: 'Raleway', sans-serif !important;
}
.gradio-container { background: #1a1a1a !important; color: #f5deb3 !important; }
.golden-heading {
  font-family: 'Playfair Display', serif !important;
  color: #ffd700 !important;
  letter-spacing: 0.08em;
}
button.primary, button.lg, .accent-bg {
  background: linear-gradient(135deg, #caa44d, #e6c85d) !important;
  color: #1a1a1a !important;
  font-weight: 700 !important;
  border: none !important;
}
textarea, input[type="text"] {
  background: #262626 !important;
  color: #f5deb3 !important;
  border: 1px solid #caa44d !important;
}
#quiz-scoreboard { color: #ffd700; text-align: right; font-family: 'Playfair Display', serif; }
.golden-panel { border: 1px solid #caa44d; padding: 8px; }
"""

QUIZ_OUTPUTS_COUNT = 7


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Sonar Mind") as demo:
        gr.HTML(f"<style>{CSS}</style>")
        gr.Markdown(
            """
<div id="header">
  <h1 class="golden-heading">Sonar Mind</h1>
  <p>Echoes of Knowledge, Made Clear</p>
</div>
"""
        )
        with gr.Tab("Transcription and indexing"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Lecture audio")
                    audio_input = gr.Audio(type="filepath", label="Upload a lecture recording")
                    transcribe_button = gr.Button("Transcribe", variant="primary")
                    transcription_input_status = gr.Textbox(label="Input status", interactive=False)
                    latest_chunk = gr.Textbox(label="Latest transcript", lines=10, interactive=False)
                    status_box = gr.Textbox(label="Status", interactive=False)
                with gr.Column():
                    gr.Markdown("### Full transcript")
                    full_transcript_box = gr.Textbox(label="Full lecture transcript", lines=18, interactive=False)
                    pasted = gr.Textbox(label="Or paste a transcript", lines=6)
                    load_paste = gr.Button("Use pasted transcript")
                    with gr.Row():
                        index_button = gr.Button("Index transcript for search", variant="primary")
                        clear_button = gr.Button("Clear transcript")
                    indexing_status = gr.Textbox(label="Indexing status", lines=2, interactive=False)
        with gr.Tab("Ask the lecture"):
            gr.Markdown("### Ask a question grounded in this lecture")
            query_box = gr.Textbox(label="Question", lines=2, placeholder="What is a foreign key?")
            ask_button = gr.Button("Ask", variant="primary")
            answer_display = gr.Markdown("The answer will appear here.")
        with gr.Tab("Quiz"):
            scoreboard = gr.Markdown("Score: 0 | Streak: 0", elem_id="quiz-scoreboard")
            gr.Markdown("Generate five questions from the indexed lecture, then answer one at a time.")
            generate_btn = gr.Button("Generate quiz", variant="primary")
            quiz_question = gr.Markdown("The question will appear here.")
            with gr.Row():
                option_button1 = gr.Button("Option 1")
                option_button2 = gr.Button("Option 2")
                option_button3 = gr.Button("Option 3")
                option_button4 = gr.Button("Option 4")
            feedback_box = gr.Textbox(label="Feedback", interactive=False)
            next_btn = gr.Button("Next question", variant="primary")
        with gr.Tab("Flashcards"):
            gr.Markdown("### Active recall")
            with gr.Row():
                flashcard_progress = gr.Markdown("0/0")
                generate_cards = gr.Button("Generate flashcards", variant="primary")
            card_question = gr.Markdown("Generate flashcards from the transcript.")
            card_answer = gr.Markdown("")
            with gr.Row():
                show_answer = gr.Button("Show Answer")
                prev_card = gr.Button("Previous")
                next_card = gr.Button("Next")
            with gr.Row():
                known_btn = gr.Button("I know this")
                unknown_btn = gr.Button("Need to review")
            card_status = gr.Textbox(label="Status", interactive=False)
        with gr.Tab("Mind map"):
            gr.Markdown("### Visual map of the lecture")
            mindmap_btn = gr.Button("Generate mind map", variant="primary")
            mindmap_display = gr.HTML("<div class='mindmap-display'><p>Generate a map after you have a transcript.</p></div>")
            mindmap_status = gr.Textbox(label="Status", interactive=False, value="Ready.")

        quiz_outputs = [quiz_question, option_button1, option_button2, option_button3, option_button4, feedback_box, scoreboard]
        card_outputs = [card_question, card_answer, card_status, flashcard_progress, show_answer]

        transcribe_button.click(
            handle_transcription_request,
            inputs=[audio_input],
            outputs=[latest_chunk, full_transcript_box, audio_input, status_box, transcription_input_status],
        )
        load_paste.click(load_pasted_transcript, inputs=[pasted], outputs=[full_transcript_box, status_box])
        index_button.click(handle_indexing_request, inputs=[full_transcript_box], outputs=[indexing_status])
        clear_button.click(handle_clear_transcript, outputs=[full_transcript_box, status_box])
        ask_button.click(handle_query_request, inputs=[query_box], outputs=[answer_display])
        generate_btn.click(generate_quiz_and_buttons, inputs=[full_transcript_box], outputs=quiz_outputs)
        option_button1.click(lambda: select_answer_and_update(0), outputs=quiz_outputs)
        option_button2.click(lambda: select_answer_and_update(1), outputs=quiz_outputs)
        option_button3.click(lambda: select_answer_and_update(2), outputs=quiz_outputs)
        option_button4.click(lambda: select_answer_and_update(3), outputs=quiz_outputs)
        next_btn.click(advance_to_next_question, outputs=quiz_outputs)
        generate_cards.click(generate_flashcards, inputs=[full_transcript_box], outputs=card_outputs)
        show_answer.click(toggle_flashcard_answer, outputs=card_outputs)
        known_btn.click(mark_card_known, outputs=card_outputs)
        unknown_btn.click(mark_card_unknown, outputs=card_outputs)
        next_card.click(advance_flashcard, outputs=card_outputs)
        prev_card.click(previous_flashcard, outputs=card_outputs)
        mindmap_btn.click(generate_mindmap, inputs=[full_transcript_box], outputs=[mindmap_display, mindmap_status])
    return demo
