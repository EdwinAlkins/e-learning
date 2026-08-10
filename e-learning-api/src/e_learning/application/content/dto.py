"""DTO — contexte ``content``."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SummaryDTO:
    summary: str


@dataclass(frozen=True, slots=True)
class TranscriptionDTO:
    content: str


@dataclass(frozen=True, slots=True)
class TranscribeCommand:
    video_id: str
    model: str = "base"
    language: str | None = None
    with_timecodes: bool = False


@dataclass(frozen=True, slots=True)
class GenerateSummaryCommand:
    video_id: str


@dataclass(frozen=True, slots=True)
class UpdateSummaryCommand:
    video_id: str
    summary: str


@dataclass(frozen=True, slots=True)
class ConvertVideosCommand:
    source_glob: str
    overwrite: bool = False


@dataclass(frozen=True, slots=True)
class IndexVideoCommand:
    video_id: str


@dataclass(frozen=True, slots=True)
class IndexDocumentCommand:
    document_id: str


@dataclass(frozen=True, slots=True)
class IndexFormationCommand:
    formation_id: str


@dataclass(frozen=True, slots=True)
class AskFormationCommand:
    formation_id: str
    question: str


@dataclass(frozen=True, slots=True)
class RagCitationDTO:
    title: str
    source: str
    excerpt: str
    video_id: str | None = None
    document_id: str | None = None


@dataclass(frozen=True, slots=True)
class AskFormationResult:
    answer: str
    citations: list[RagCitationDTO]


@dataclass(frozen=True, slots=True)
class IndexFormationResult:
    indexed_videos: int
    indexed_chunks: int
    indexed_documents: int = 0
