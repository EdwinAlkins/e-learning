"""Extraction de la consommation depuis une réponse OpenAI-compatible."""

from __future__ import annotations

from typing import Any

from e_learning.application.shared.llm import LlmUsage


def usage_from_response(response: Any, *, fallback_model: str) -> LlmUsage | None:
    """``None`` si le serveur ne renvoie pas le bloc ``usage`` (certains serveurs locaux)."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    return LlmUsage(
        model=getattr(response, "model", None) or fallback_model,
        prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
        completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
    )
