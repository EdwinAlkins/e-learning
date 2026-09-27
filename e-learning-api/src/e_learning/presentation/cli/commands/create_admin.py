"""Commande : créer un compte administrateur sans redémarrer l'API."""

from __future__ import annotations

import asyncio

import click

from e_learning.application.user.dto import CreateUserCommand
from e_learning.application.user.use_cases.create_user import CreateUser
from e_learning.domain.shared.exceptions import DomainError
from e_learning.infrastructure.persistence.user.repository import SqlAlchemyUserRepository
from e_learning.infrastructure.security.password_hasher import Argon2PasswordHasher
from e_learning.presentation.cli.session import transactional_session


@click.command("create-admin")
@click.option("--email", required=True, help="Email du compte")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Mot de passe (demandé si absent, jamais affiché)",
)
@click.option("--full-name", default=None, help="Nom affiché")
def create_admin_cmd(email: str, password: str, full_name: str | None) -> None:
    """Crée un compte administrateur."""
    try:
        user = asyncio.run(_create_admin(email, password, full_name))
    except DomainError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Administrateur créé : {user}")


async def _create_admin(email: str, password: str, full_name: str | None) -> str:
    async with transactional_session() as session:
        dto = await CreateUser(SqlAlchemyUserRepository(session), Argon2PasswordHasher()).execute(
            CreateUserCommand(email=email, password=password, full_name=full_name, is_admin=True)
        )
    return f"{dto.email} ({dto.id})"
