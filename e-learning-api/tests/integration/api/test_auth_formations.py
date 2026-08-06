"""Tests d'intégration API (auth + formations)."""

from __future__ import annotations

from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "health ok"


async def test_generate_and_list_formations(client: AsyncClient) -> None:
    auth = await client.post("/auth/generate")
    assert auth.status_code == 200
    uid = auth.json()["uid"]
    assert uid

    create = await client.post("/formations", json={"name": "Python"}, headers={"X-User-UID": uid})
    assert create.status_code == 201
    formation_id = create.json()["id"]

    listing = await client.get("/formations")
    assert listing.status_code == 200
    names = [f["name"] for f in listing.json()["formations"]]
    assert "Python" in names

    detail = await client.get(f"/formations/{formation_id}")
    assert detail.status_code == 200
    assert detail.json()["slug"]


async def test_notes_require_auth(client: AsyncClient) -> None:
    response = await client.get("/notes/00000000-0000-7000-8000-000000000099")
    assert response.status_code == 401
