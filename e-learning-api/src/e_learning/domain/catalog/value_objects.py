"""Value objects du bounded context ``catalog``."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from e_learning.domain.catalog.exceptions import (
    EmptyName,
    EmptySlug,
    InvalidChapterId,
    InvalidDocumentId,
    InvalidDuration,
    InvalidFormationId,
    InvalidJobId,
    InvalidPosition,
    InvalidRelativePath,
    InvalidVideoId,
    NameTooLong,
)

NAME_MAX_LENGTH = 255
SLUG_MAX_LENGTH = 255
_SLUG_SAFE = re.compile(r"[^a-z0-9._-]+")


def slugify(raw: str) -> str:
    """Produit un slug FS-safe à partir d'un libellé."""
    cleaned = raw.strip().lower().replace(" ", "-")
    cleaned = _SLUG_SAFE.sub("-", cleaned).strip("-._")
    return cleaned[:SLUG_MAX_LENGTH] or "item"


@dataclass(frozen=True, slots=True)
class FormationId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> FormationId:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> FormationId:
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidFormationId(raw) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ChapterId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> ChapterId:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> ChapterId:
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidChapterId(raw) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class VideoId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> VideoId:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> VideoId:
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidVideoId(raw) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class DocumentId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> DocumentId:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> DocumentId:
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidDocumentId(raw) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class FormationName:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise EmptyName()
        if len(cleaned) > NAME_MAX_LENGTH:
            raise NameTooLong(NAME_MAX_LENGTH)
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ChapterName:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise EmptyName()
        if len(cleaned) > NAME_MAX_LENGTH:
            raise NameTooLong(NAME_MAX_LENGTH)
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class VideoTitle:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise EmptyName()
        if len(cleaned) > NAME_MAX_LENGTH:
            raise NameTooLong(NAME_MAX_LENGTH)
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class DocumentTitle:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise EmptyName()
        if len(cleaned) > NAME_MAX_LENGTH:
            raise NameTooLong(NAME_MAX_LENGTH)
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Slug:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise EmptySlug()
        if len(cleaned) > SLUG_MAX_LENGTH:
            cleaned = cleaned[:SLUG_MAX_LENGTH]
        object.__setattr__(self, "value", cleaned)

    @classmethod
    def from_name(cls, name: str) -> Slug:
        return cls(slugify(name))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Position:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidPosition()

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class JobId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> JobId:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> JobId:
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidJobId(raw) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class DurationSeconds:
    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidDuration()


@dataclass(frozen=True, slots=True)
class RelativePath:
    """Chemin relatif sous ``APP_VIDEOS_PATH`` (séparateur ``/``)."""

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip().replace("\\", "/").lstrip("/")
        if not cleaned:
            raise EmptySlug()
        if ".." in cleaned.split("/"):
            raise InvalidRelativePath(cleaned)
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value
