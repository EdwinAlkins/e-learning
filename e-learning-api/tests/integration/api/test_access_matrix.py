"""Matrice route × rôle : 401 sans jeton, 403 apprenant sur le studio, 2xx sinon."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute, RouteContext, iter_route_contexts
from httpx import AsyncClient

from e_learning.infrastructure.persistence.catalog.models import (
    ChapterModel,
    DocumentModel,
    FormationModel,
    VideoModel,
)
from e_learning.presentation.api.dependencies.auth import get_current_user, require_admin
from tests.integration.conftest import bearer

PUBLIC_ROUTES = {
    ("POST", "/auth/login"),
    ("POST", "/auth/logout"),
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/ready"),
    ("GET", "/metrics"),
}

LEARNER_ROUTES = {
    ("GET", "/auth/me"),
    ("PATCH", "/auth/me/password"),
    ("GET", "/formations"),
    ("GET", "/formations/{formation_id}"),
    ("POST", "/formations/{formation_id}/ask"),
    ("GET", "/videos/{video_id}/stream"),
    ("GET", "/videos/{video_id}/file"),
    ("GET", "/videos/{video_id}/summary"),
    ("GET", "/videos/{video_id}/transcription"),
    ("GET", "/docs/chapters/{chapter_id}"),
    ("GET", "/docs/{document_id}/file"),
    ("GET", "/notes/{video_id}"),
    ("POST", "/notes/{video_id}"),
    ("PUT", "/notes/{note_id}"),
    ("DELETE", "/notes/{note_id}"),
    ("GET", "/progress/formations"),
    ("GET", "/progress/formation/{formation_id}"),
    ("GET", "/progress/{video_id}"),
    ("POST", "/progress/{video_id}"),
    ("GET", "/usage"),
}

ADMIN_ROUTES = {
    ("POST", "/formations"),
    ("PATCH", "/formations/{formation_id}"),
    ("DELETE", "/formations/{formation_id}"),
    ("POST", "/formations/{formation_id}/chapters"),
    ("PUT", "/formations/{formation_id}/chapters/order"),
    ("POST", "/formations/{formation_id}/index"),
    ("PATCH", "/chapters/{chapter_id}"),
    ("DELETE", "/chapters/{chapter_id}"),
    ("PUT", "/chapters/{chapter_id}/videos/order"),
    ("POST", "/chapters/{chapter_id}/videos"),
    ("POST", "/chapters/{chapter_id}/docs"),
    ("PATCH", "/chapters/{chapter_id_source}/{chapter_id_target}/{video_id}"),
    ("PATCH", "/videos/{video_id}"),
    ("DELETE", "/videos/{video_id}"),
    ("PUT", "/videos/{video_id}/summary"),
    ("POST", "/videos/{video_id}/summary/generate"),
    ("POST", "/videos/{video_id}/transcription"),
    ("POST", "/videos/{video_id}/conversion"),
    ("PATCH", "/docs/{document_id}"),
    ("DELETE", "/docs/{document_id}"),
    ("GET", "/admin/users"),
    ("POST", "/admin/users"),
    ("PATCH", "/admin/users/{user_id}"),
    ("DELETE", "/admin/users/{user_id}"),
}


def _api_routes(app: Any) -> list[tuple[str, str, RouteContext]]:
    """Routes effectives (préfixe et dépendances des routeurs inclus appliqués)."""
    return [
        (method, context.path, context)
        for context in iter_route_contexts(app.routes)
        if isinstance(context.original_route, APIRoute)
        for method in sorted((context.methods or set()) - {"HEAD"})
    ]


def _depends_on(dependant: Dependant, target: object) -> bool:
    return any(d.call is target or _depends_on(d, target) for d in dependant.dependencies)


def _fill(path: str) -> str:
    return re.sub(r"\{[^}]+\}", lambda _: str(uuid4()), path)


def test_route_inventory_matches_the_access_matrix(app: Any) -> None:
    """Toute nouvelle route doit être classée ici : oubli = échec du test."""
    declared = {(method, path) for method, path, _ in _api_routes(app)}
    assert declared == PUBLIC_ROUTES | LEARNER_ROUTES | ADMIN_ROUTES


def test_every_non_public_route_has_an_auth_dependency(app: Any) -> None:
    unguarded = [
        (method, path)
        for method, path, route in _api_routes(app)
        if (method, path) not in PUBLIC_ROUTES
        and not _depends_on(route.dependant, get_current_user)
    ]
    assert unguarded == []

    admin_guarded = {
        (method, path)
        for method, path, route in _api_routes(app)
        if _depends_on(route.dependant, require_admin)
    }
    assert admin_guarded == ADMIN_ROUTES


@pytest.mark.parametrize(("method", "path"), sorted(LEARNER_ROUTES | ADMIN_ROUTES))
async def test_non_public_routes_require_a_token(
    client: AsyncClient, method: str, path: str
) -> None:
    response = await client.request(method, _fill(path))
    assert response.status_code == 401, response.text
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(("method", "path"), sorted(ADMIN_ROUTES))
async def test_admin_routes_are_forbidden_to_learners(
    client: AsyncClient, learner_token: str, method: str, path: str
) -> None:
    response = await client.request(method, _fill(path), headers=bearer(learner_token))
    assert response.status_code == 403, response.text


@dataclass
class Catalog:
    formation_id: str
    chapter_id: str
    video_id: str
    document_id: str
    video_bytes: bytes


async def seed_catalog(app: Any) -> Catalog:
    """Formation → chapitre → vidéo prête (+ résumé, transcription) et document."""
    formation_id, chapter_id, video_id, document_id = uuid4(), uuid4(), uuid4(), uuid4()
    slug = f"matrix-{formation_id.hex[:8]}"
    root: Path = app.state.settings.videos_path / slug / "chap"
    root.mkdir(parents=True)
    video_bytes = bytes(range(256)) * 16
    (root / "intro.mp4").write_bytes(video_bytes)
    (root / "intro.md").write_text("# Résumé", encoding="utf-8")
    (root / "intro.txt").write_text("transcription", encoding="utf-8")
    (root / "support.pdf").write_bytes(b"%PDF-1.4")

    async with app.state.session_factory() as session:
        session.add(FormationModel(id=formation_id, name=slug, slug=slug))
        await session.flush()
        session.add(
            ChapterModel(
                id=chapter_id, formation_id=formation_id, name="Chap", slug="chap", position=0
            )
        )
        await session.flush()
        session.add(
            VideoModel(
                id=video_id,
                chapter_id=chapter_id,
                title="Intro",
                filename="intro.mp4",
                relative_path=f"{slug}/chap/intro.mp4",
                position=0,
                duration_seconds=10.0,
            )
        )
        await session.flush()
        session.add(
            DocumentModel(
                id=document_id,
                chapter_id=chapter_id,
                video_id=video_id,
                title="Support",
                filename="support.pdf",
                relative_path=f"{slug}/chap/support.pdf",
                mime_type="application/pdf",
                position=0,
            )
        )
        await session.commit()
    return Catalog(str(formation_id), str(chapter_id), str(video_id), str(document_id), video_bytes)


@pytest.mark.parametrize("role", ["learner", "admin"])
async def test_learner_routes_succeed_for_every_authenticated_role(
    app: Any, client: AsyncClient, learner_token: str, admin_token: str, role: str
) -> None:
    catalog = await seed_catalog(app)
    headers = bearer(learner_token if role == "learner" else admin_token)
    f, c, v, d = catalog.formation_id, catalog.chapter_id, catalog.video_id, catalog.document_id

    ok_calls: list[tuple[str, str, dict[str, Any]]] = [
        ("GET", "/auth/me", {}),
        ("GET", "/formations", {}),
        ("GET", f"/formations/{f}", {}),
        ("GET", f"/videos/{v}/stream", {}),
        ("GET", f"/videos/{v}/file", {}),
        ("GET", f"/videos/{v}/summary", {}),
        ("GET", f"/videos/{v}/transcription", {}),
        ("GET", f"/docs/chapters/{c}", {}),
        ("GET", f"/docs/{d}/file", {}),
        ("GET", f"/notes/{v}", {}),
        ("GET", "/progress/formations", {}),
        ("GET", f"/progress/formation/{f}", {}),
        ("POST", f"/progress/{v}", {"json": {"last_position": 3.5}}),
        ("GET", f"/progress/{v}", {}),
        ("GET", "/usage", {}),
    ]
    for method, url, kwargs in ok_calls:
        response = await client.request(method, url, headers=headers, **kwargs)
        assert 200 <= response.status_code < 300, (method, url, response.text)

    created = await client.post(
        f"/notes/{v}", json={"timecode": 1.0, "content": "Note"}, headers=headers
    )
    assert created.status_code == 201
    note_id = created.json()["id"]
    updated = await client.put(f"/notes/{note_id}", json={"content": "Edit"}, headers=headers)
    assert updated.status_code == 200
    assert (await client.delete(f"/notes/{note_id}", headers=headers)).status_code == 204

    # RAG : dépend de Qdrant et du LLM, absents ici. On vérifie seulement que
    # l'autorisation passe (ni 401 ni 403).
    ask = await client.post(f"/formations/{f}/ask", json={"question": "?"}, headers=headers)
    assert ask.status_code not in (401, 403)


async def test_admin_can_run_studio_writes(app: Any, client: AsyncClient, admin_token: str) -> None:
    """Chaîne d'écritures studio sans dépendance externe (ni RabbitMQ, ni ffmpeg, ni LLM)."""
    catalog = await seed_catalog(app)
    headers = bearer(admin_token)
    v = catalog.video_id

    formation = await client.post(
        "/formations", json={"name": f"Studio {uuid4().hex[:6]}"}, headers=headers
    )
    assert formation.status_code == 201, formation.text
    f = formation.json()["id"]
    renamed = await client.patch(
        f"/formations/{f}", json={"name": f"Studio {uuid4().hex[:6]}"}, headers=headers
    )
    assert renamed.status_code == 200, renamed.text

    chapters = []
    for name in ("Un", "Deux"):
        chapter = await client.post(
            f"/formations/{f}/chapters", json={"name": name}, headers=headers
        )
        assert chapter.status_code == 201, chapter.text
        chapters.append(chapter.json()["id"])
    reorder = await client.put(
        f"/formations/{f}/chapters/order",
        json={"chapter_ids": list(reversed(chapters))},
        headers=headers,
    )
    assert reorder.status_code == 200, reorder.text
    rename_chapter = await client.patch(
        f"/chapters/{chapters[0]}", json={"name": "Premier"}, headers=headers
    )
    assert rename_chapter.status_code == 200, rename_chapter.text

    doc = await client.post(
        f"/chapters/{chapters[0]}/docs",
        data={"title": "Fiche"},
        files={"file": ("fiche.md", b"# Fiche", "text/markdown")},
        headers=headers,
    )
    assert doc.status_code == 201, doc.text
    doc_id = doc.json()["id"]
    patched = await client.patch(f"/docs/{doc_id}", json={"title": "Fiche 2"}, headers=headers)
    assert patched.status_code == 200, patched.text
    assert (await client.delete(f"/docs/{doc_id}", headers=headers)).status_code == 204

    summary = await client.put(
        f"/videos/{v}/summary", json={"summary": "# Nouveau"}, headers=headers
    )
    assert summary.status_code == 200, summary.text
    reorder_videos = await client.put(
        f"/chapters/{catalog.chapter_id}/videos/order", json={"video_ids": [v]}, headers=headers
    )
    assert reorder_videos.status_code == 200, reorder_videos.text

    assert (await client.delete(f"/chapters/{chapters[1]}", headers=headers)).status_code == 204
    assert (await client.delete(f"/formations/{f}", headers=headers)).status_code == 204
    assert (await client.delete(f"/videos/{v}", headers=headers)).status_code == 204
