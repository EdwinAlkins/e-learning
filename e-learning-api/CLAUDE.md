# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

API e-learning en **architecture hexagonale (ports & adapters)** et **DDD tactique**.
Bounded contexts : `user`, `catalog`, `learning`, `content`.

Stack: FastAPI · SQLAlchemy 2 async · PostgreSQL (asyncpg) · Pydantic v2 · pytest · ruff · mypy · uv · import-linter.
Python **≥ 3.14** (UUIDv7 stdlib).

## Commands

```bash
uv sync --group ai --group dev

# API
uv run hypercorn e_learning.main:app --reload
# ou
uv run e-learning-api

# Worker (jobs RabbitMQ : conversion, transcription, résumé, RAG)
uv run e-learning-worker
# ou
uv run python -m e_learning.presentation.worker

# CLI
uv run e-learning-cli reconcile              # régénère le catalogue FS ↔ DB
uv run e-learning-cli list-videos            # liste les UUID vidéos
uv run e-learning-cli transcribe -v <uuid>
uv run e-learning-cli summary -v <uuid>      # alias: resume
uv run e-learning-cli convert --glob '**/*.*'

# Tests
uv run pytest
uv run pytest tests/unit/
uv run pytest tests/integration/   # Docker requis (testcontainers)

# Qualité
uv run ruff check .
uv run ruff format .
uv run mypy
uv run lint-imports

# Migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

## Architecture

Règle de dépendance (import-linter) :
`presentation → infrastructure → application → domain`

Package `src/e_learning/` :

- **domain/** — entités, VO (UUIDv7), exceptions sémantiques, ports repository
- **application/** — use cases + DTO dataclasses + ports techniques (storage, media, summary, messaging…)
- **infrastructure/** — SQLAlchemy async, FS catalogue, Whisper/LLM, ffmpeg, RabbitMQ, config `APP_*`
- **presentation/** — API FastAPI (composition root DI) + CLI Click + **worker** (consumer RabbitMQ)

### Bounded contexts

| Contexte | Agrégats / rôle |
|----------|-----------------|
| `user` | Utilisateur anonyme (`UserId` UUIDv7) |
| `catalog` | Formation, Chapter, Video, Document, Job — `position` en base, slugs FS stables |
| `learning` | Note, Progress (FK vers user + video) |
| `content` | Transcription / résumé / conversion / RAG |

### Auth

Header `X-User-UID: <uuid>`. En `APP_DEBUG=true`, fallback UID fixe si header absent.
OpenAPI UI : `/api-docs` (debug only).

### Catalogue

- Identités UUIDv7 (plus de SHA1 path)
- Ordre = colonne `position` (reorder sans renommer toute la série)
- `relative_path` unique = clé de réconciliation FS↔DB
- `ReconcileCatalog` au démarrage **uniquement** si `APP_RECONCILE_ON_STARTUP=true` (sinon via CLI)

### Jobs de calcul

Les jobs lourds (conversion, transcription, résumé, index RAG) sont publiés sur RabbitMQ
(`JobPublisherPort`) après commit HTTP, et exécutés par le process `e-learning-worker`
(prefetch paramétrable via `APP_WORKER_PREFETCH`, défaut 3).

## Configuration (`APP_` prefix)

| Variable | Défaut | Rôle |
|----------|--------|------|
| `APP_DATABASE_URL` | postgres local | URL asyncpg |
| `APP_VIDEOS_PATH` | `videos/` | Racine FS |
| `APP_DEBUG` | `false` | docs UI + UID fallback |
| `APP_INIT_DB` | `false` | `create_all` au boot |
| `APP_RECONCILE_ON_STARTUP` | `false` | reconcile FS↔DB au boot (sinon `e-learning-cli reconcile`) |
| `APP_SUMMARY_STRATEGY` | `openapi` | `openapi` \| `gemini` |
| `APP_RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | Broker jobs |
| `APP_RABBITMQ_EXCHANGE` | `elearning_jobs` | Exchange DIRECT |
| `APP_WORKER_PREFETCH` | `3` | Concurrence max par process worker |

## Docker

```bash
docker compose up -d postgres rabbitmq
uv run alembic upgrade head
uv run e-learning-api
uv run e-learning-worker

# stack complète
docker compose up --build
```
