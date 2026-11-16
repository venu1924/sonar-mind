"""Shared Gemini chat helper that returns parsed JSON."""

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from sonar_mind.config import GEMINI_MODEL, get_api_key
from sonar_mind.json_tools import parse_model_json


def make_llm(temperature: float = 0.1) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=temperature,
        max_retries=2,
        google_api_key=get_api_key(),
    )


def generate_json(template: str, transcript: str, temperature: float = 0.1):
    prompt = PromptTemplate.from_template(template)
    message = prompt.format(transcript=transcript)
    response = make_llm(temperature).invoke(message)
    content = response.content if hasattr(response, "content") else response
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    return parse_model_json(content)
