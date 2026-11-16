"""Runtime configuration. Secrets come from the environment, never from source."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# The capstone report called gemini-2.0-flash and models/text-embedding-004.
# Those Gemini API models are retired. These are the current replacements.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
GEMINI_EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-2")
PERSIST_DIRECTORY = str(ROOT / "chroma_db")


def get_api_key() -> str:
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add a Gemini API key, "
            "or add the same name as a secret on Hugging Face Spaces."
        )
    return key
