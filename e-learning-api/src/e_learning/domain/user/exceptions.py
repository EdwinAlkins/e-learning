"""Exceptions métier du bounded context ``user``."""

from __future__ import annotations

from e_learning.domain.shared.exceptions import NotFoundError, ValidationError


class InvalidUserId(ValidationError):
    def __init__(self, raw: str) -> None:
        self.raw = raw
        super().__init__(f"Identifiant d'utilisateur invalide : {raw!r}.")


class UserNotFound(NotFoundError):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"Aucun utilisateur trouvé pour l'identifiant {user_id}.")
