"""Gemini AI client wrapper.

A thin service around the google-genai SDK. It centralizes client creation,
model selection, and error handling so the rest of the codebase has a single
well-typed entry point for talking to Gemini — and so swapping the model (or
provider) later touches exactly one file.
"""

from __future__ import annotations

from functools import lru_cache

from django.conf import settings
from google import genai
from google.genai import errors, types


class AIClientError(Exception):
    """Raised when a call to the Gemini API fails or returns nothing usable."""


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Return a process-wide cached Gemini client built from settings."""
    if not settings.GEMINI_API_KEY:
        raise AIClientError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_text(
    prompt: str,
    *,
    config: types.GenerateContentConfig | None = None,
) -> str:
    """Send a prompt to Gemini and return the model's text response.

    `config` carries generation options (temperature, JSON mode, a response
    schema, etc.) and is how Step 3 will request structured output. The SDK
    already retries transient errors (429/5xx) with backoff, so an APIError
    reaching us is a genuine failure.

    Raises:
        AIClientError: on API failure or an empty response.
    """
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
    except errors.APIError as exc:
        raise AIClientError(f"Gemini request failed: {exc}") from exc

    text = response.text
    if not text:
        raise AIClientError("Gemini returned an empty response.")

    return text