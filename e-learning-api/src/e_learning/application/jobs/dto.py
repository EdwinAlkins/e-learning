"""DTO messages queue — jobs de calcul (contrat validé application)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Self

from e_learning.domain.catalog.job import Job

COMPUTE_JOB_KINDS = frozenset(
    {
        Job.KIND_MEDIA_CONVERSION,
        Job.KIND_TRANSCRIPTION,
        Job.KIND_SUMMARY,
        Job.KIND_RAG_INDEX_VIDEO,
        Job.KIND_RAG_INDEX_FORMATION,
    }
)

_KINDS_REQUIRING_VIDEO = frozenset(
    {
        Job.KIND_MEDIA_CONVERSION,
        Job.KIND_TRANSCRIPTION,
        Job.KIND_SUMMARY,
        Job.KIND_RAG_INDEX_VIDEO,
    }
)

_KINDS_REQUIRING_FORMATION = frozenset({Job.KIND_RAG_INDEX_FORMATION})


def routing_key_for(kind: str) -> str:
    return f"job.{kind}"


@dataclass(frozen=True, slots=True)
class ComputeJobMessage:
    """Message de job de calcul — validé à la construction / désérialisation."""

    job_id: str
    kind: str
    video_id: str | None = None
    formation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.job_id or not str(self.job_id).strip():
            raise ValueError("ComputeJobMessage.job_id est requis")
        if self.kind not in COMPUTE_JOB_KINDS:
            raise ValueError(
                f"ComputeJobMessage.kind invalide : {self.kind!r} "
                f"(attendu : {sorted(COMPUTE_JOB_KINDS)})"
            )
        if self.kind in _KINDS_REQUIRING_VIDEO and not self.video_id:
            raise ValueError(f"ComputeJobMessage.video_id requis pour kind={self.kind}")
        if self.kind in _KINDS_REQUIRING_FORMATION and not self.formation_id:
            raise ValueError(f"ComputeJobMessage.formation_id requis pour kind={self.kind}")

    @property
    def routing_key(self) -> str:
        return routing_key_for(self.kind)

    def to_dict(self) -> dict[str, Any]:
        """Sérialisation filaire (adaptateur broker uniquement)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Désérialise et valide un payload broker."""
        if not isinstance(data, dict):
            raise ValueError(f"Payload job invalide (dict attendu) : {type(data).__name__}")
        try:
            job_id = data["job_id"]
            kind = data["kind"]
        except KeyError as exc:
            raise ValueError(f"Payload job incomplet, champ manquant : {exc.args[0]}") from exc
        video_id = data.get("video_id")
        formation_id = data.get("formation_id")
        return cls(
            job_id=str(job_id).strip(),
            kind=str(kind).strip(),
            video_id=str(video_id).strip() if video_id else None,
            formation_id=str(formation_id).strip() if formation_id else None,
        )
