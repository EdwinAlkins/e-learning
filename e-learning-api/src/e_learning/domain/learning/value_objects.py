"""Value objects du bounded context ``learning``."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from e_learning.domain.learning.exceptions import (
    EmptyNoteContent,
    InvalidLastPosition,
    InvalidNoteId,
    InvalidProgressId,
    InvalidTimecode,
)


@dataclass(frozen=True, slots=True)
class NoteId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> NoteId:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> NoteId:
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidNoteId(raw) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ProgressId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> ProgressId:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> ProgressId:
        try:
            return cls(uuid.UUID(raw))
        except ValueError as exc:
            raise InvalidProgressId(raw) from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class TimecodeSeconds:
    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidTimecode()


@dataclass(frozen=True, slots=True)
class LastPositionSeconds:
    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidLastPosition()


@dataclass(frozen=True, slots=True)
class NoteContent:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise EmptyNoteContent()
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value
