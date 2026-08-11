"""Tests — réécriture des relative_path."""

from e_learning.application.catalog.relative_paths import rewrite_path_prefix


def test_rewrite_path_prefix_formation() -> None:
    assert (
        rewrite_path_prefix("old-slug/chapter/video.mp4", "old-slug", "new-slug")
        == "new-slug/chapter/video.mp4"
    )


def test_rewrite_path_prefix_chapter() -> None:
    assert (
        rewrite_path_prefix(
            "formation/1-old/doc.pdf",
            "formation/1-old",
            "formation/1-new",
        )
        == "formation/1-new/doc.pdf"
    )


def test_rewrite_path_prefix_ignores_unrelated() -> None:
    assert rewrite_path_prefix("other/a.mp4", "old-slug", "new-slug") is None
    assert rewrite_path_prefix("old-slugger/a.mp4", "old-slug", "new-slug") is None
