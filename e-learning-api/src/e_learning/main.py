"""Point d'entrée ASGI / Hypercorn."""

from __future__ import annotations

from e_learning.presentation.api.app import create_app

app = create_app()


def run() -> None:
    """Lance Hypercorn (entry-point ``e-learning-api``)."""
    import asyncio

    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8000"]
    asyncio.run(serve(app, config))


if __name__ == "__main__":
    run()
