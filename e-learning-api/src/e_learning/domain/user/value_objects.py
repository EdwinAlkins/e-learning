"""Value objects du bounded context ``user``."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from e_learning.domain.user.exceptions import InvalidEmail, InvalidUserId

# Volontairement permissif : une partie locale, un @, un domaine avec au moins un point.
# La preuve qu'une adresse existe relève d'un envoi de mail, pas d'une regex.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_EMAIL_MAX_LENGTH = 320


@dataclass(frozen=True, slots=True)
class UserId:
    """Identité d'un utilisateur (UUIDv7)."""

    value: uuid.UUID

    @classmethod
    def generate(cls) -> UserId:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> UserId:
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidUserId(raw) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class Email:
    """Adresse email normalisée (espaces retirés, minuscules)."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if len(normalized) > _EMAIL_MAX_LENGTH or not _EMAIL_RE.match(normalized):
            raise InvalidEmail(self.value)
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
