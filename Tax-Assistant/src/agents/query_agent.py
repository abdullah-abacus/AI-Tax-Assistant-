"""
General Query Agent using Gemini 2.5 Pro (direct SDK client)
Answers user questions about KRA tax concepts and procedures.
"""
import os
from typing import Dict, Any

from google import genai
from google.genai import types

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Single shared Gemini client (no PEP 604 union to keep Python 3.11 happy)
GENAI_CLIENT = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

QUERY_INSTRUCTION = """You are the General Tax Query Agent for KRA Tax Assistant.

Your role is to answer questions about Kenyan tax concepts, procedures, and forms.

CRITICAL RULES:
- If the user says they are "not filing yet", you are only answering a general question.
- Do NOT ask for personal identifiers (KRA PIN, ID number, phone, email).
- Do NOT pretend to see user-specific KRA records or previous filings.
- Base your answers on general Kenyan tax rules and the IT1 / VAT3 forms.
- Be clear, concise, and use simple examples with KES amounts where helpful.
- If the question is unclear, ask a short follow-up question to clarify.
"""


def _get_client() -> genai.Client:
    """Get a shared Gemini client using API key from environment."""
    if GENAI_CLIENT is None:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Please configure it in your environment."
        )
    return GENAI_CLIENT


def answer_tax_question(user_id: str, question: str) -> str:
    """
    Use Gemini to answer a general tax question.

    Args:
        user_id: Chat/session identifier.
        question: User's natural-language question.

    Returns:
        Model text response.
    """
    client = _get_client()

    # Keep this fairly small so responses come back faster
    config = types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=400,
        top_p=0.95,
    )

    # Combine system instruction + user question into one content call
    prompt = f"{QUERY_INSTRUCTION}\n\nUser question:\n{question}"

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=config,
    )

    # The SDK returns a GenerateContentResponse; text is in .text
    return response.text or ""


