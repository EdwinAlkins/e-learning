"""Ports techniques du contexte ``user`` (hachage, jetons, anti-bruteforce)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass


class PasswordHasher(ABC):
    """Hachage des mots de passe. Asynchrone : les algorithmes lents tournent hors boucle."""

    @abstractmethod
    async def hash(self, password: str) -> str: ...

    @abstractmethod
    async def verify(self, password: str, hashed_password: str | None) -> bool:
        """Vérifie ``password`` contre ``hashed_password``.

        ``None`` compare contre un hash factice et renvoie toujours ``False`` :
        le temps de réponse ne révèle pas si le compte existe.
        """


@dataclass(frozen=True, slots=True)
class IssuedToken:
    """Jeton émis par le service de jetons."""
    access_token: str
    expires_in: int
    """Durée de validité en secondes."""


class TokenService(ABC):
    @abstractmethod
    def issue(self, subject: str) -> IssuedToken: ...

    @abstractmethod
    def decode(self, token: str) -> str:
        """Renvoie le ``sub`` du jeton ; lève ``InvalidCredentials`` sinon."""


class LoginThrottle(ABC):
    """Limitation des échecs de connexion par clé (email, IP…)."""

    @abstractmethod
    async def retry_after(self, keys: Sequence[str]) -> int | None:
        """Secondes à attendre si l'une des clés est bloquée, sinon ``None``."""

    @abstractmethod
    async def record_failure(self, keys: Sequence[str]) -> None: ...

    @abstractmethod
    async def reset(self, key: str) -> None: ...
