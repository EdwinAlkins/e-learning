"""Politique de mot de passe (le domaine ne voit jamais le mot de passe en clair)."""

from __future__ import annotations

from e_learning.domain.user.exceptions import InvalidPassword

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def check_password_policy(password: str) -> None:
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise InvalidPassword(PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH)
