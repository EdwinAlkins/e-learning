"""Adaptateur PasswordHasher — argon2 via pwdlib."""

from __future__ import annotations

import asyncio

from pwdlib import PasswordHash

from e_learning.application.user.ports import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    """Hachage argon2 via pwdlib, exécuté hors de la boucle d'événements.

    ``_dummy_hash`` est calculé au démarrage à partir d'une chaîne fixe.
    Ce n'est pas un mot de passe de compte : le hash n'est pas enregistré,
    un sel aléatoire le recrée à chaque processus, et ``verify`` ignore
    le résultat pour renvoyer ``False``. Il sert quand l'email est inconnu,
    afin de payer le même coût argon2 qu'un mauvais mot de passe. Le délai
    de réponse ne révèle donc pas si le compte existe.
    """

    def __init__(self) -> None:
        self._hash = PasswordHash.recommended()
        self._dummy_hash = self._hash.hash("dummy-password-for-constant-time")

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._hash.hash, password)

    async def verify(self, password: str, hashed_password: str | None) -> bool:
        """Compare ``password`` au hash stocké.

        ``hashed_password is None`` (compte absent) : la comparaison se fait
        contre ``_dummy_hash``, puis la méthode renvoie toujours ``False``.
        Connaître la chaîne source ne permet pas de se connecter.
        """
        if hashed_password is None:
            await asyncio.to_thread(self._hash.verify, password, self._dummy_hash)
            return False
        return await asyncio.to_thread(self._hash.verify, password, hashed_password)
