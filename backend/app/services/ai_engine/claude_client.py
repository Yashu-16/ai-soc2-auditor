"""
Thin wrapper around the Anthropic Claude API.

Kept deliberately small and isolated so the provider could be swapped
(e.g. for OpenAI) by replacing only this file — nothing else in the
codebase should import `anthropic` directly.
"""

import json
from typing import Any

from anthropic import Anthropic

from app.core.config import get_settings

settings = get_settings()
_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to backend/.env before "
                "calling the AI engine."
            )
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def call_claude_json(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> Any:
    """
    Calls Claude with a system+user prompt and expects a JSON response.
    Returns the parsed JSON (list or dict), or raises ValueError if the
    response can't be parsed — callers are responsible for retry/fallback
    logic, this function does not retry internally.
    """
    client = get_client()
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    raw_text = "".join(text_parts).strip()

    # Strip markdown code fences if the model wrapped its JSON in them,
    # despite being told not to — defensive, not relied upon.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude response was not valid JSON: {e}\nRaw: {raw_text[:500]}")