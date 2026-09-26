"""Exceptions métier du bounded context ``usage``."""

from __future__ import annotations

from e_learning.domain.shared.exceptions import ValidationError


class InvalidTokenUsageId(ValidationError):
    def __init__(self, raw: str) -> None:
        self.raw = raw
        super().__init__(f"Identifiant de consommation invalide : {raw!r}.")


class InvalidTokenCount(ValidationError):
    def __init__(self, field: str, value: int) -> None:
        self.field = field
        self.value = value
        super().__init__(f"Nombre de tokens invalide pour {field} : {value}.")


class InvalidUsageKind(ValidationError):
    def __init__(self, kind: str) -> None:
        self.kind = kind
        super().__init__(f"Type de consommation LLM inconnu : {kind!r}.")
