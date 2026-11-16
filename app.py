"""Hugging Face Spaces and local entry point.

Spaces reads the Gradio object named `demo`. The API key must be a secret
named GOOGLE_API_KEY. It is never written into this file.
"""

from sonar_mind.ui import build_app

demo = build_app()

if __name__ == "__main__":
    demo.launch()
