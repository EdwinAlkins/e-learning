# Trois étages finaux :
#   - `migrate` : alembic seul, sans la chaîne IA ni ffmpeg (~250 Mo) ;
#   - `api`     : cible par défaut, sert aussi au worker (commande différente).
#
# Les étages sont ordonnés « stable d'abord » : le venv change quand les
# dépendances changent, `src/` à chaque commit. Copier le venv avant les
# sources évite de réécrire plusieurs Go de calque à chaque modification.

############################
# Dépendances — noyau
############################
FROM python:3.14-slim-trixie AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:0.12.2 /uv /uvx /bin/
COPY pyproject.toml ./
COPY README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv venv --python 3.14 /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Dépendances de base uniquement : alembic, SQLAlchemy, asyncpg, FastAPI.
# C'est tout ce dont `migrate` a besoin.
RUN uv pip install .

############################
# Dépendances — groupe « ai »
############################
FROM builder AS builder-ai

# Ajoute openai-whisper, sentence-transformers et qdrant-client dans le même
# venv. torch est résolu depuis l'index CPU de PyTorch (voir [tool.uv.sources]
# dans pyproject.toml) : sans cela, l'index PyPI livre la variante CUDA, soit
# ~3,2 Go de bibliothèques `nvidia-*` et ~900 Mo de `triton` que ce
# déploiement n'utilise jamais — aucun service ne réserve de GPU.
RUN uv pip install --group ai .

############################
# Base runtime commune
############################
FROM python:3.14-slim-trixie AS runtime-base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"

############################
# migrate — alembic seul
############################
FROM runtime-base AS migrate

COPY --from=builder /opt/venv /opt/venv
COPY alembic ./alembic
COPY alembic.ini ./
COPY src ./src

CMD ["alembic", "upgrade", "head"]

############################
# api / worker — chaîne IA
############################
FROM runtime-base AS api

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Poids des modèles : jamais embarqués dans l'image, téléchargés au premier
# usage. `HF_HOME` couvre sentence-transformers, `XDG_CACHE_HOME` couvre
# openai-whisper (qui écrit dans `$XDG_CACHE_HOME/whisper`). Les deux sont
# montés en volume par compose : sans cela, chaque recréation de conteneur
# retélécharge le modèle.
ENV HF_HOME=/cache/huggingface \
    XDG_CACHE_HOME=/cache
RUN mkdir -p /cache/huggingface /cache/whisper

COPY --from=builder-ai /opt/venv /opt/venv
COPY alembic ./alembic
COPY alembic.ini ./
COPY src ./src

EXPOSE 8000
CMD ["hypercorn", "e_learning.main:app", "--bind", "0.0.0.0:8000"]
