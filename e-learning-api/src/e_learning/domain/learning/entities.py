"""Entités du bounded context ``learning``."""

from __future__ import annotations

from datetime import UTC, datetime

from e_learning.domain.catalog.value_objects import VideoId
from e_learning.domain.learning.value_objects import (
    LastPositionSeconds,
    NoteContent,
    NoteId,
    ProgressId,
    TimecodeSeconds,
)
from e_learning.domain.user.value_objects import UserId


def _now() -> datetime:
    return datetime.now(UTC)


class Note:
    def __init__(
        self,
        *,
        id: NoteId,
        user_id: UserId,
        video_id: VideoId,
        timecode: TimecodeSeconds,
        content: NoteContent,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.video_id = video_id
        self.timecode = timecode
        self.content = content
        self.created_at = created_at

    @classmethod
    def create(
        cls,
        *,
        user_id: UserId,
        video_id: VideoId,
        timecode: TimecodeSeconds,
        content: NoteContent,
    ) -> Note:
        return cls(
            id=NoteId.generate(),
            user_id=user_id,
            video_id=video_id,
            timecode=timecode,
            content=content,
            created_at=_now(),
        )

    def update_content(self, content: NoteContent) -> None:
        self.content = content

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Note) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)


class Progress:
    def __init__(
        self,
        *,
        id: ProgressId,
        user_id: UserId,
        video_id: VideoId,
        last_position: LastPositionSeconds,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.video_id = video_id
        self.last_position = last_position
        self.updated_at = updated_at

    @classmethod
    def create(
        cls,
        *,
        user_id: UserId,
        video_id: VideoId,
        last_position: LastPositionSeconds,
    ) -> Progress:
        return cls(
            id=ProgressId.generate(),
            user_id=user_id,
            video_id=video_id,
            last_position=last_position,
            updated_at=_now(),
        )

    def update_position(self, last_position: LastPositionSeconds) -> None:
        self.last_position = last_position
        self.updated_at = _now()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Progress) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
