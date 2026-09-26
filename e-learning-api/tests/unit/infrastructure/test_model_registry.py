"""Les FK des modèles se résolvent sans charger l'app FastAPI (worker, CLI)."""

from __future__ import annotations

import subprocess
import sys

import pytest

_CHECK = """
import importlib
importlib.import_module({module!r})
from e_learning.infrastructure.persistence.database import Base
for table in Base.metadata.tables.values():
    for fk in table.foreign_keys:
        fk.column  # lève NoReferencedTableError si la table cible n'est pas enregistrée
"""


@pytest.mark.parametrize(
    "module",
    [
        "e_learning.presentation.worker.handlers",
        "e_learning.presentation.cli.commands.summary",
    ],
)
def test_foreign_keys_resolve_from_entrypoint_imports(module: str) -> None:
    # Interpréteur neuf : les autres tests ont déjà importé tous les modèles
    result = subprocess.run(
        [sys.executable, "-c", _CHECK.format(module=module)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
