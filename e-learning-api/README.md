# E-Learning API

API FastAPI pour la plateforme e-learning — **architecture hexagonale / DDD**.

## Prérequis

- Python ≥ 3.14
- [uv](https://docs.astral.sh/uv/)
- Docker (Postgres + tests d'intégration)

## Démarrage rapide

```bash
cp .env.template .env
docker compose up -d postgres
uv sync --group ai --group dev
uv run alembic upgrade head
uv run hypercorn e_learning.main:app --reload
```

CLI :

```bash
uv run e-learning-cli reconcile
uv run e-learning-cli transcribe --video-id <uuid>
uv run e-learning-cli resume --video-id <uuid>
uv run e-learning-cli convert
```

Voir [CLAUDE.md](CLAUDE.md) pour l'architecture et [API.md](API.md) pour les endpoints.
