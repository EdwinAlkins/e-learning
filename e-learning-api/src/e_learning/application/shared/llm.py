"""Résultat d'un appel LLM : texte généré + consommation de tokens."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LlmUsage:
    model: str
    prompt_tokens: int
    completion_tokens: int


@dataclass(frozen=True, slots=True)
class LlmCompletion:
    """``usage`` vaut ``None`` quand le fournisseur ne remonte pas les tokens (gemini-cli)."""

    text: str
    usage: LlmUsage | None = None
