"""Shared Claude call wrapper with the typed-exception error handling chain
(most-specific-first, per Anthropic SDK guidance) factored out so rag.py
and digest.py don't each reimplement it.
"""
from __future__ import annotations

import logging

import anthropic

from config import ANTHROPIC_MODEL

log = logging.getLogger("claude_client")


class ClaudeCallError(Exception):
    """A user-facing message explaining why a Claude call failed."""


def call_claude(system: str, user_content: str, max_tokens: int = 1024, effort: str = "low") -> str:
    client = anthropic.Anthropic()
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            output_config={"effort": effort},
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.AuthenticationError as exc:
        raise ClaudeCallError("Claude API authentication failed - check ANTHROPIC_API_KEY.") from exc
    except anthropic.RateLimitError as exc:
        retry_after = exc.response.headers.get("retry-after", "a few seconds")
        raise ClaudeCallError(f"Rate limited - try again in {retry_after}.") from exc
    except anthropic.APIConnectionError as exc:
        raise ClaudeCallError("Could not reach the Claude API - check your network connection.") from exc
    except anthropic.APIStatusError as exc:
        log.exception("Claude API error")
        raise ClaudeCallError(f"Claude API error ({exc.status_code}): {exc.message}") from exc

    return next((block.text for block in response.content if block.type == "text"), "")
