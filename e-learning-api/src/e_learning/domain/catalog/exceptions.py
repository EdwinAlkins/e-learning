"""Exceptions métier du bounded context ``catalog``."""

from __future__ import annotations

from e_learning.domain.shared.exceptions import ConflictError, NotFoundError, ValidationError


class InvalidFormationId(ValidationError):
    def __init__(self, raw: str) -> None:
        super().__init__(f"Identifiant de formation invalide : {raw!r}.")


class InvalidChapterId(ValidationError):
    def __init__(self, raw: str) -> None:
        super().__init__(f"Identifiant de chapitre invalide : {raw!r}.")


class InvalidVideoId(ValidationError):
    def __init__(self, raw: str) -> None:
        super().__init__(f"Identifiant de vidéo invalide : {raw!r}.")


class InvalidDocumentId(ValidationError):
    def __init__(self, raw: str) -> None:
        super().__init__(f"Identifiant de document invalide : {raw!r}.")


class InvalidJobId(ValidationError):
    def __init__(self, raw: str) -> None:
        super().__init__(f"Identifiant de job invalide : {raw!r}.")


class JobNotFound(NotFoundError):
    def __init__(self, job_id: str) -> None:
        super().__init__(f"Aucun job trouvé pour l'identifiant {job_id}.")


class EmptyName(ValidationError):
    def __init__(self) -> None:
        super().__init__("Le nom ne peut pas être vide.")


class NameTooLong(ValidationError):
    def __init__(self, max_length: int) -> None:
        super().__init__(f"Le nom ne peut pas dépasser {max_length} caractères.")


class EmptySlug(ValidationError):
    def __init__(self) -> None:
        super().__init__("Le slug ne peut pas être vide.")


class InvalidPosition(ValidationError):
    def __init__(self) -> None:
        super().__init__("La position doit être un entier >= 0.")


class InvalidDuration(ValidationError):
    def __init__(self) -> None:
        super().__init__("La durée doit être >= 0.")


class InvalidRelativePath(ValidationError):
    def __init__(self, raw: str) -> None:
        self.raw = raw
        super().__init__(f"Chemin relatif invalide : {raw!r}.")


class FormationNotFound(NotFoundError):
    def __init__(self, formation_id: str) -> None:
        super().__init__(f"Aucune formation trouvée pour l'identifiant {formation_id}.")


class ChapterNotFound(NotFoundError):
    def __init__(self, chapter_id: str) -> None:
        super().__init__(f"Aucun chapitre trouvé pour l'identifiant {chapter_id}.")


class VideoNotFound(NotFoundError):
    def __init__(self, video_id: str) -> None:
        super().__init__(f"Aucune vidéo trouvée pour l'identifiant {video_id}.")


class DocumentNotFound(NotFoundError):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Aucun document trouvé pour l'identifiant {document_id}.")


class FormationNameAlreadyUsed(ConflictError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Le nom de formation {name!r} est déjà utilisé.")


class FormationSlugAlreadyUsed(ConflictError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Le slug de formation {slug!r} est déjà utilisé.")


class ReorderInvalid(ValidationError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class UnsupportedFileExtension(ValidationError):
    def __init__(self, filename: str, *, allowed: frozenset[str]) -> None:
        ordered = ", ".join(sorted(allowed))
        super().__init__(
            f"Extension non autorisée pour {filename!r}. "
            f"Extensions acceptées : {ordered}."
        )


class MediaNotReady(ConflictError):
    def __init__(self, video_id: str, status: str) -> None:
        super().__init__(f"Média non disponible (statut={status}) : {video_id}")


class AiJobConflict(ConflictError):
    def __init__(self, video_id: str, job: str, status: str) -> None:
        super().__init__(f"Job {job} déjà en cours ou invalide (statut={status}) : {video_id}")


class TranscriptionNotReady(ConflictError):
    def __init__(self, video_id: str) -> None:
        super().__init__(f"Transcription requise avant de générer le résumé : {video_id}")
