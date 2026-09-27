"""Exceptions métier du bounded context ``user``."""

from __future__ import annotations

from e_learning.domain.shared.exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)


class InvalidUserId(ValidationError):
    def __init__(self, raw: str) -> None:
        self.raw = raw
        super().__init__(f"Identifiant d'utilisateur invalide : {raw!r}.")


class InvalidEmail(ValidationError):
    def __init__(self, raw: str) -> None:
        self.raw = raw
        super().__init__(f"Adresse email invalide : {raw!r}.")


class InvalidPassword(ValidationError):
    """Le mot de passe ne respecte pas la politique de longueur."""

    def __init__(self, min_length: int, max_length: int) -> None:
        super().__init__(
            f"Le mot de passe doit contenir entre {min_length} et {max_length} caractères."
        )


class UserNotFound(NotFoundError):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"Aucun utilisateur trouvé pour l'identifiant {user_id}.")


class EmailAlreadyUsed(ConflictError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Un compte existe déjà pour l'email {email}.")


class InvalidCredentials(DomainError):
    """Identifiants ou jeton invalides (message volontairement générique)."""

    def __init__(self, message: str = "Identifiants invalides.") -> None:
        super().__init__(message)


class InactiveUser(DomainError):
    def __init__(self) -> None:
        super().__init__("Compte désactivé.")


class AdminRequired(DomainError):
    def __init__(self) -> None:
        super().__init__("Accès réservé aux administrateurs.")


class IncorrectPassword(DomainError):
    """Mot de passe actuel erroné lors d'un changement de mot de passe.

    Distinct de :class:`InvalidCredentials` : l'utilisateur reste authentifié,
    le client ne doit pas le déconnecter.
    """

    def __init__(self) -> None:
        super().__init__("Mot de passe actuel incorrect.")


class SelfLockout(ConflictError):
    """Un admin tente de se retirer ses droits, se désactiver ou se supprimer."""

    def __init__(self, action: str) -> None:
        self.action = action
        super().__init__(f"Un administrateur ne peut pas {action} son propre compte.")


class TooManyLoginAttempts(DomainError):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Trop de tentatives de connexion. Réessayez plus tard.")
