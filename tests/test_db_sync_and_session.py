from __future__ import annotations

import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from sqlalchemy import Boolean, DateTime, Float, Integer, Numeric, String

try:
    from tests.support import FakeResult, FakeSession, FakeSessionFactory, ROOT_DIR
except ModuleNotFoundError:
    from support import FakeResult, FakeSession, FakeSessionFactory, ROOT_DIR

from trovabenzina.db import session as db_session
from trovabenzina.db import sync as db_sync
from trovabenzina.db.models import Fuel

TMP_ROOT = ROOT_DIR / "TMP"


def ensure_case_dir(name: str) -> Path:
    path = TMP_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return path


class FakeConnection:
    def __init__(self, *, execute_side_effect=None):
        self.execute = AsyncMock(side_effect=execute_side_effect)
        self.exec_driver_sql = AsyncMock()
        self.run_sync = AsyncMock()


class FakeBeginContext:
    def __init__(self, connection: FakeConnection):
        self.connection = connection

    async def __aenter__(self) -> FakeConnection:
        return self.connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class SyncHelperTests(unittest.IsolatedAsyncioTestCase):
    def test_as_bool_and_cast_for_column(self):
        self.assertTrue(db_sync._as_bool(" yes "))
        self.assertFalse(db_sync._as_bool("off"))

        self.assertEqual(db_sync._cast_for_column(Numeric(), "1.23"), Decimal("1.23"))
        self.assertEqual(db_sync._cast_for_column(Integer(), "7"), 7)
        self.assertEqual(db_sync._cast_for_column(Float(), "3.5"), 3.5)
        self.assertEqual(db_sync._cast_for_column(Boolean(), "true"), True)
        self.assertEqual(db_sync._cast_for_column(DateTime(), "2025-01-01T00:00:00"), "2025-01-01T00:00:00")
        self.assertEqual(db_sync._cast_for_column(String(), "hello"), "hello")
        self.assertIsNone(db_sync._cast_for_column(String(), ""))
        self.assertEqual(db_sync._cast_for_column(Integer(), "not-an-int"), "not-an-int")

    def test_model_columns_map_parse_row_and_value_compare(self):
        cols = db_sync._model_columns_map(Fuel)
        self.assertIn("code", cols)
        self.assertIn("avg_consumption_per_100km", cols)

        parsed = db_sync._parse_csv_row_for_model(
            Fuel,
            {
                "code": "1",
                "name": "gasoline",
                "uom": "liter",
                "avg_consumption_per_100km": "7.0",
                "ignored": "value",
            },
        )
        self.assertEqual(
            parsed,
            {
                "name": "gasoline",
                "uom": "liter",
                "avg_consumption_per_100km": Decimal("7.0"),
            },
        )
        self.assertTrue(db_sync._values_differ("a", "b"))
        self.assertFalse(db_sync._values_differ("a", "a"))

    async def test_load_csv_map_handles_missing_empty_duplicates_and_missing_codes(self):
        root = ensure_case_dir("test_load_csv_map")

        missing = await db_sync._load_csv_map(str(root / "missing.csv"))
        self.assertEqual(missing, ({}, [], [], 0))

        empty_path = root / "empty.csv"
        empty_path.write_text("\n\n", encoding="utf-8")
        empty = await db_sync._load_csv_map(str(empty_path))
        self.assertEqual(empty, ({}, [], [], 0))

        csv_path = root / "fuels.csv"
        csv_path.write_text(
            "code,name\n"
            "1,gasoline\n"
            ",missing\n"
            "1,gasoline-updated\n"
            "2,diesel\n",
            encoding="utf-8",
        )

        code_map, headers, duplicate_codes, missing_code_rows = await db_sync._load_csv_map(str(csv_path))
        self.assertEqual(headers, ["code", "name"])
        self.assertEqual(duplicate_codes, ["1"])
        self.assertEqual(missing_code_rows, 1)
        self.assertEqual(code_map["1"]["name"], "gasoline-updated")
        self.assertEqual(code_map["2"]["name"], "diesel")

    async def test_sync_model_from_csv_inserts_updates_restores_and_soft_deletes(self):
        active = Fuel(code="1", name="gasoline-old", uom="liter", avg_consumption_per_100km=Decimal("6.5"))
        active.del_ts = None
        removed = Fuel(code="2", name="diesel", uom="liter", avg_consumption_per_100km=Decimal("5.0"))
        removed.del_ts = None
        restored = Fuel(code="3", name="cng", uom="kilo", avg_consumption_per_100km=Decimal("4.0"))
        restored.del_ts = datetime(2025, 1, 1, tzinfo=timezone.utc)

        fake_session = FakeSession(execute_results=[FakeResult(scalars=[active, removed, restored])])
        factory = FakeSessionFactory(fake_session)

        root = ensure_case_dir("test_sync_model_from_csv")
        csv_path = root / "fuels.csv"
        csv_path.write_text(
            "code,name,uom,avg_consumption_per_100km\n"
            "1,gasoline,liter,7.0\n"
            "3,cng,kilo,4.0\n"
            "4,lpg,liter,8.0\n",
            encoding="utf-8",
        )

        with (
            patch.object(db_sync, "ASSETS_CSV_DIR", root),
            patch.object(db_sync, "AsyncSession", factory),
        ):
            await db_sync._sync_model_from_csv(Fuel, "fuels.csv")

        self.assertEqual(fake_session.commit_count, 1)
        self.assertEqual(len(fake_session.added), 1)
        self.assertEqual(fake_session.added[0].code, "4")
        self.assertEqual(fake_session.added[0].name, "lpg")
        self.assertEqual(active.name, "gasoline")
        self.assertEqual(active.avg_consumption_per_100km, Decimal("7.0"))
        self.assertIsNotNone(removed.del_ts)
        self.assertIsNone(restored.del_ts)

    async def test_sync_config_tables_calls_both_domain_syncs(self):
        with patch.object(db_sync, "_sync_model_from_csv", new=AsyncMock()) as sync_model:
            await db_sync.sync_config_tables()

        sync_model.assert_has_awaits(
            [
                unittest.mock.call(db_sync.Fuel, "fuels.csv"),
                unittest.mock.call(db_sync.Language, "languages.csv"),
            ]
        )


class SessionHelperTests(unittest.IsolatedAsyncioTestCase):
    def test_split_sql_naive(self):
        self.assertEqual(
            db_session._split_sql_naive("SELECT 1;  ; SELECT 2 ;"),
            ["SELECT 1", "SELECT 2"],
        )

    async def test_execute_sql_scripts_dir_skips_missing_directory(self):
        with patch.object(db_session, "engine", SimpleNamespace(begin=Mock())) as engine:
            await db_session._execute_sql_scripts_dir(Path("C:/not-existing-dir"))
        engine.begin.assert_not_called()

    async def test_execute_sql_scripts_dir_executes_single_statement_files(self):
        connection = FakeConnection()
        engine = SimpleNamespace(begin=Mock(return_value=FakeBeginContext(connection)))

        sql_dir = ensure_case_dir("test_execute_sql_single")
        (sql_dir / "001-test.sql").write_text("SELECT 1", encoding="utf-8")

        with patch.object(db_session, "engine", engine):
            await db_session._execute_sql_scripts_dir(sql_dir)

        connection.execute.assert_awaited_once()
        connection.exec_driver_sql.assert_not_awaited()

    async def test_execute_sql_scripts_dir_falls_back_to_statement_split(self):
        single_connection = FakeConnection(execute_side_effect=RuntimeError("single statement failed"))
        split_connection = FakeConnection()
        engine = SimpleNamespace(
            begin=Mock(
                side_effect=[
                    FakeBeginContext(single_connection),
                    FakeBeginContext(split_connection),
                ]
            )
        )

        sql_dir = ensure_case_dir("test_execute_sql_split")
        (sql_dir / "001-test.sql").write_text("SELECT 1; SELECT 2;", encoding="utf-8")

        with patch.object(db_session, "engine", engine):
            await db_session._execute_sql_scripts_dir(sql_dir)

        self.assertEqual(engine.begin.call_count, 2)
        single_connection.execute.assert_awaited_once()
        split_connection.exec_driver_sql.assert_awaited()
        self.assertEqual(split_connection.exec_driver_sql.await_count, 2)
        self.assertEqual(split_connection.exec_driver_sql.await_args_list[0].args[0], "SELECT 1")
        self.assertEqual(split_connection.exec_driver_sql.await_args_list[1].args[0], "SELECT 2")

    async def test_init_db_sets_timezone_creates_tables_and_executes_assets(self):
        connection = FakeConnection()
        engine = SimpleNamespace(begin=Mock(return_value=FakeBeginContext(connection)))

        with (
            patch.object(db_session, "engine", engine),
            patch.object(db_session, "_execute_sql_scripts_dir", new=AsyncMock()) as execute_sql_dir,
        ):
            await db_session.init_db()

        connection.execute.assert_awaited_once()
        self.assertEqual(str(connection.execute.await_args.args[0]), "SET TIME ZONE 'Europe/Rome';")
        connection.run_sync.assert_awaited_once()
        execute_sql_dir.assert_awaited_once_with(db_session.ASSETS_SQL_DIR)

    def test_route_support_migration_sql_exists(self):
        migration_path = db_session.ASSETS_SQL_DIR / "003-ALTER_TABLE_searches_route_support.sql"
        self.assertTrue(migration_path.exists())
        migration_sql = migration_path.read_text(encoding="utf-8")
        self.assertIn("DO $$", migration_sql)
        self.assertIn("to_regclass('searches')", migration_sql)
        self.assertIn("ALTER COLUMN radius DROP NOT NULL", migration_sql)
        self.assertIn("ADD COLUMN IF NOT EXISTS search_type", migration_sql)


if __name__ == "__main__":
    unittest.main()
