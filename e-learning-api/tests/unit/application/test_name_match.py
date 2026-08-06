"""Tests — association document ↔ vidéo par nom."""

from __future__ import annotations

from e_learning.application.catalog.name_match import (
    find_matching_video,
    normalize_media_name,
    strip_order_prefix,
)
from e_learning.domain.catalog.entities import Video
from e_learning.domain.catalog.value_objects import (
    ChapterId,
    DurationSeconds,
    Position,
    RelativePath,
    VideoTitle,
)


def test_strip_order_prefix() -> None:
    assert strip_order_prefix("1. Les Fondations") == "Les Fondations"
    assert strip_order_prefix("2-La Projection") == "La Projection"
    assert strip_order_prefix("3_Intro") == "Intro"
    assert strip_order_prefix("Sans préfixe") == "Sans préfixe"


def test_normalize_media_name() -> None:
    assert normalize_media_name("1. Les Fondations") == "les fondations"
    assert normalize_media_name("  Les   Fondations  ") == "les fondations"
    assert normalize_media_name("2.Fixation d'objectifs") == "fixation d'objectifs"


def test_find_matching_video_by_title() -> None:
    chapter_id = ChapterId.generate()
    video = Video.create(
        chapter_id=chapter_id,
        title=VideoTitle("Les Fondations"),
        filename="1. Les Fondations.mp4",
        relative_path=RelativePath("f/c/1. Les Fondations.mp4"),
        position=Position(0),
        duration=DurationSeconds(10),
    )
    matched = find_matching_video([video], "1. Les Fondations")
    assert matched is video
    assert find_matching_video([video], "Fixation d'objectifs") is None


def test_find_matching_video_by_filename_stem() -> None:
    chapter_id = ChapterId.generate()
    video = Video.create(
        chapter_id=chapter_id,
        title=VideoTitle("Autre titre"),
        filename="1. Les Fondations.mp4",
        relative_path=RelativePath("f/c/1. Les Fondations.mp4"),
        position=Position(0),
        duration=DurationSeconds(10),
    )
    assert find_matching_video([video], "Les Fondations") is video
