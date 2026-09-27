# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

API e-learning en **architecture hexagonale (ports & adapters)** et **DDD tactique**.
Bounded contexts : `user`, `catalog`, `learning`, `content`, `usage`.

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
uv run e-learning-cli create-admin --email admin@example.com   # mot de passe demandé

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
| `user` | Compte (email, hash argon2, `is_admin`, `is_active`) — `UserId` UUIDv7 |
| `catalog` | Formation, Chapter, Video, Document, Job — `position` en base, slugs FS stables |
| `learning` | Note, Progress (FK vers user + video) |
| `content` | Transcription / résumé / conversion / RAG |
| `usage` | TokenUsage — journal append-only des tokens LLM par utilisateur (`token_usage`) |

### Auth

Login OAuth2 password (`POST /auth/login`, email dans `username`) → JWT HS256 (`sub`, `iat`, `exp`).
Jeton accepté en `Authorization: Bearer` ou cookie `access_token` (web ; écritures par cookie →
header `X-Requested-With` exigé, anti-CSRF). Le compte est relu en base à chaque requête.

- Routes fermées par défaut : chaque routeur déclare `dependencies=[Depends(get_current_user)]`
  ou `[Depends(require_admin)]` (`presentation/api/dependencies/auth.py`). Toute écriture du
  catalogue va dans `studio_router` (`routers/studio.py`), chemins inchangés.
- `tests/integration/api/test_access_matrix.py` liste chaque route avec son rôle : une nouvelle
  route non classée ou non gardée fait échouer la CI.
- Ports `PasswordHasher` / `TokenService` / `LoginThrottle` (`application/user/ports.py`),
  adaptateurs dans `infrastructure/security/` (pwdlib argon2, pyjwt, fenêtre glissante en mémoire
  — par process).
- Premier admin créé au démarrage (`APP_FIRST_ADMIN_*`, idempotent) ; sinon
  `e-learning-cli create-admin --email <email>`.
- Démarrage refusé hors debug si `APP_SECRET_KEY` / `APP_FIRST_ADMIN_PASSWORD` valent
  `changethis` (ou clé < 32 caractères), et toujours si `APP_CORS_ORIGINS` contient `*`.

OpenAPI UI : `/api-docs` (debug only), bouton *Authorize* branché sur `/auth/login`.

### Catalogue

- Identités UUIDv7 (plus de SHA1 path)
- Ordre = colonne `position` (reorder sans renommer toute la série)
- `relative_path` unique = clé de réconciliation FS↔DB
- `ReconcileCatalog` au démarrage **uniquement** si `APP_RECONCILE_ON_STARTUP=true` (sinon via CLI)

### Jobs de calcul

Les jobs lourds (conversion, transcription, résumé, index RAG) sont publiés sur RabbitMQ
(`JobPublisherPort`) après commit HTTP, et exécutés par le process `e-learning-worker`
(prefetch paramétrable via `APP_WORKER_PREFETCH`, défaut 3).

### Consommation LLM

`ChatPort.answer` / `SummaryPort.generate` renvoient un `LlmCompletion` (texte + `LlmUsage`
optionnel). Les use cases `AskFormation` et `GenerateSummary` journalisent l'usage via
`record_llm_usage` dans la même transaction. Le `user_id` du demandeur d'un résumé voyage
dans `Job.user_id` et `ComputeJobMessage.user_id` jusqu'au worker. Les résumés lancés en CLI
sont enregistrés avec `user_id = NULL`. Non comptés : gemini-cli (pas de décompte), embeddings.
Lecture : `GET /usage?days=30` (1–365) — totaux fenêtre + cumul, détail par type / modèle / jour (UTC).

## Configuration (`APP_` prefix)

| Variable | Défaut | Rôle |
|----------|--------|------|
| `APP_DATABASE_URL` | postgres local | URL asyncpg |
| `APP_VIDEOS_PATH` | `videos/` | Racine FS |
| `APP_DEBUG` | `false` | docs UI ; tolère les secrets d'exemple (avertissement) |
| `APP_INIT_DB` | `false` | `create_all` au boot |
| `APP_RECONCILE_ON_STARTUP` | `false` | reconcile FS↔DB au boot (sinon `e-learning-cli reconcile`) |
| `APP_SUMMARY_STRATEGY` | `openapi` | `openapi` \| `gemini` |
| `APP_RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | Broker jobs |
| `APP_RABBITMQ_EXCHANGE` | `elearning_jobs` | Exchange DIRECT |
| `APP_WORKER_PREFETCH` | `3` | Concurrence max par process worker |
| `APP_SECRET_KEY` | `changethis` | Clé JWT HS256 (≥ 32 caractères hors debug) |
| `APP_ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | Validité du jeton (7 jours, pas de refresh) |
| `APP_FIRST_ADMIN_EMAIL` | `admin@example.com` | Premier admin créé au démarrage |
| `APP_FIRST_ADMIN_PASSWORD` | `changethis` | Son mot de passe initial (refusé hors debug) |
| `APP_LOGIN_MAX_FAILURES` / `APP_LOGIN_WINDOW_MINUTES` | `5` / `15` | Anti-bruteforce login → 429 |
| `APP_INSECURE_COOKIE_HOSTS` | `["localhost","127.0.0.1","::1"]` | Hôtes où le cookie n'est pas `Secure` en HTTP (ex. IP d'un serveur LAN) |

## Docker

```bash
docker compose up -d postgres rabbitmq
uv run alembic upgrade head
uv run e-learning-api
uv run e-learning-worker

# stack complète
docker compose up --build
```

`docker/Dockerfile` expose deux cibles :

| Cible | Contenu | Services |
|-------|---------|----------|
| `migrate` | alembic + SQLAlchemy + asyncpg, sans groupe `ai` ni ffmpeg (~180 Mo) | `migrate` |
| `api` | cible par défaut, groupe `ai` complet + ffmpeg (~1,9 Go) | `api`, `worker` |

torch est résolu depuis l'index CPU de PyTorch et `triton` est exclu
(`[tool.uv.sources]` / `[tool.uv]` dans `pyproject.toml`) : aucun service ne
réserve de GPU, la pile CUDA pesait 4 Go pour rien. Ne pas retirer ces réglages
sans ajouter une réservation de device dans compose.
