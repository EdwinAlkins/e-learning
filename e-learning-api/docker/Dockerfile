FROM python:3.14-slim-trixie AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
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
# Groupe « ai » : openai-whisper + openai (transcription / résumé depuis l'API)
RUN uv pip install --group ai .

FROM python:3.14-slim-trixie AS api

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    libpq5 \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY alembic ./alembic
COPY alembic.ini ./
COPY src ./src
COPY --from=ghcr.io/astral-sh/uv:0.12.2 /uv /uvx /bin/

EXPOSE 8000
CMD ["hypercorn", "e_learning.main:app", "--bind", "0.0.0.0:8000"]
