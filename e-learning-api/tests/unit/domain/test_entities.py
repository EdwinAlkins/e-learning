"""Tests unitaires — domaine user / catalog."""

from __future__ import annotations

import uuid

import pytest

from e_learning.domain.catalog.entities import Formation, Video
from e_learning.domain.catalog.exceptions import EmptyName, InvalidPosition
from e_learning.domain.catalog.value_objects import (
    ChapterId,
    DurationSeconds,
    FormationName,
    Position,
    RelativePath,
    VideoTitle,
)
from e_learning.domain.user.entities import User
from e_learning.domain.user.value_objects import UserId


def test_user_create_uses_uuid7() -> None:
    user = User.create()
    assert isinstance(user.id.value, uuid.UUID)
    assert user.id.value.version == 7


def test_user_id_from_string_roundtrip() -> None:
    user = User.create()
    restored = UserId.from_string(str(user.id))
    assert restored == user.id


def test_formation_rename() -> None:
    formation = Formation.create(name=FormationName("Algo"))
    formation.rename(FormationName("Algorithmes"))
    assert str(formation.name) == "Algorithmes"


def test_empty_name_rejected() -> None:
    with pytest.raises(EmptyName):
        FormationName("  ")


def test_position_must_be_non_negative() -> None:
    with pytest.raises(InvalidPosition):
        Position(-1)


def test_video_relocate() -> None:
    video = Video.create(
        chapter_id=ChapterId.generate(),
        title=VideoTitle("Intro"),
        filename="intro.mp4",
        relative_path=RelativePath("f/c/intro.mp4"),
        position=Position(0),
        duration=DurationSeconds(10.0),
    )
    new_chapter = ChapterId.generate()
    video.relocate(
        chapter_id=new_chapter,
        position=Position(2),
        relative_path=RelativePath("f/c2/intro.mp4"),
    )
    assert video.chapter_id == new_chapter
    assert video.position.value == 2
