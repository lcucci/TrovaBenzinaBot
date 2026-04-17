from __future__ import annotations

"""
Database session and initialization helpers.

This module exposes:
- `engine`: the async SQLAlchemy engine (asyncpg for PostgreSQL).
- `AsyncSession`: session factory for async ORM use.
- `init_db()`: idempotent database initializer (tables + optional SQL scripts).

Notes:
    - Only entity models (tables) must be registered on `Base` before
      `create_all()`. View models should inherit from `ViewBase` and are not
      created by `create_all()`, so they won't clash with CREATE VIEW.
"""

import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from ..config import DATABASE_URL
from .models.base import Base

log = logging.getLogger(__name__)

# Project root and SQL assets directory
BASE_DIR = Path(__file__).resolve().parents[3]
ASSETS_SQL_DIR = BASE_DIR / "assets" / "config" / "sql"

# Normalize URL to async driver if it's plain "postgresql"
_url = make_url(DATABASE_URL)
if _url.drivername == "postgresql":
    _url = _url.set(drivername="postgresql+asyncpg")

# Async engine and session factory
engine = create_async_engine(_url, echo=False, pool_pre_ping=True, future=True)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)


def _split_sql_naive(sql: str) -> list[str]:
    """Naively split a SQL script into statements by ';'.

    Warning:
        This splitter is safe for simple DDL like CREATE VIEW statements.
        It is NOT suitable for complex scripts with functions/procedures,
        dollar-quoted bodies, or semicolons inside string literals.

    Args:
        sql: Raw SQL script content.

    Returns:
        List of statements without trailing semicolons and surrounding whitespace.
    """
    return [s.strip() for s in sql.split(";") if s.strip()]


async def _execute_sql_scripts_dir(dir_path: Path) -> None:
    """Execute all .sql files in a directory, sorted by filename.

    For each file:
        - Try to execute as a single statement.
        - If it fails, retry in a fresh transaction with a naive statement split.

    Args:
        dir_path: Directory containing .sql files.
    """
    if not dir_path.exists():
        log.info("SQL assets directory not found: %s", dir_path)
        return

    sql_files = sorted(dir_path.glob("*.sql"))
    if not sql_files:
        log.info("No SQL scripts to execute under: %s", dir_path)
        return

    for sql_file in sql_files:
        raw = sql_file.read_text(encoding="utf-8").strip()
        if not raw:
            continue

        try:
            async with engine.begin() as conn:
                # Fast path: single-statement file
                await conn.execute(text(raw))
            log.info("Executed SQL script: %s", sql_file.name)
        except Exception as e:
            log.warning(
                "Single-statement execution failed for %s (%s). "
                "Falling back to naive split.",
                sql_file.name,
                e,
            )
            statements = _split_sql_naive(raw)
            async with engine.begin() as conn:
                for stmt in statements:
                    try:
                        # `exec_driver_sql` bypasses SQLAlchemy SQL compiler
                        await conn.exec_driver_sql(stmt)
                    except Exception as inner:
                        log.error(
                            "Error executing statement from %s:\n---\n%s\n---\n%s",
                            sql_file.name,
                            stmt,
                            inner,
                        )
                        raise
            log.info("Executed SQL script (split): %s", sql_file.name)


async def init_db() -> None:
    """Initialize database: set session timezone, create tables, run SQL assets.

    Steps:
        1) Set session time zone to Europe/Rome (server-side).
        2) Create all tables from SQLAlchemy metadata (`Base.metadata.create_all`).
        3) Execute optional SQL scripts (e.g., CREATE OR REPLACE VIEW ...).

    Notes:
        - Ensure that only *table* models inherit from `Base`. View models
          must inherit from `ViewBase` and won't be created by `create_all()`.
        - SQL scripts are executed within a transaction; failing statements will
          abort the transaction and raise, making the deploy fail fast.
    """
    # Step 1: set TZ and create tables
    async with engine.begin() as conn:
        # Force session timezone (affects NOW(), etc.)
        await conn.execute(text("SET TIME ZONE 'Europe/Rome';"))

        # Create tables for all mapped classes on Base
        await conn.run_sync(Base.metadata.create_all)

    # Step 2: execute SQL assets (e.g., create/replace views)
    await _execute_sql_scripts_dir(ASSETS_SQL_DIR)
