"""Configuración global de tests.

Los tests borran tablas completas, así que NUNCA deben apuntar al Postgres de desarrollo.
Se fuerza una base SQLite aislada antes de importar la app (database.py lee DATABASE_URL al importarse).
Para correr contra Postgres de pruebas: TEST_DATABASE_URL=postgresql+asyncpg://... pytest
"""

import os
from pathlib import Path

_TEST_DB = Path(__file__).resolve().parent / "test.db"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", f"sqlite+aiosqlite:///{_TEST_DB}"
)
