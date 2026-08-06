"""Exceptions métier du bounded context ``learning``."""

from __future__ import annotations

from e_learning.domain.shared.exceptions import NotFoundError, ValidationError


class InvalidNoteId(ValidationError):
    def __init__(self, raw: str) -> None:
        super().__init__(f"Identifiant de note invalide : {raw!r}.")


class InvalidProgressId(ValidationError):
    def __init__(self, raw: str) -> None:
        super().__init__(f"Identifiant de progression invalide : {raw!r}.")


class InvalidTimecode(ValidationError):
    def __init__(self) -> None:
        super().__init__("Le timecode doit être >= 0.")


class InvalidLastPosition(ValidationError):
    def __init__(self) -> None:
        super().__init__("La position de lecture doit être >= 0.")


class EmptyNoteContent(ValidationError):
    def __init__(self) -> None:
        super().__init__("Le contenu de la note ne peut pas être vide.")


class NoteNotFound(NotFoundError):
    def __init__(self, note_id: str) -> None:
        super().__init__(f"Aucune note trouvée pour l'identifiant {note_id}.")


class ProgressNotFound(NotFoundError):
    def __init__(self, progress_id: str) -> None:
        super().__init__(f"Aucune progression trouvée pour l'identifiant {progress_id}.")
