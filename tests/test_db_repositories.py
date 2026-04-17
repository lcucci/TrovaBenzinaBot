from __future__ import annotations

import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

try:
    from tests.support import FakeResult, FakeSession, FakeSessionFactory
except ModuleNotFoundError:
    from support import FakeResult, FakeSession, FakeSessionFactory

from trovabenzina.config import DEFAULT_LANGUAGE
from trovabenzina.db.models import BroadcastMessage, Fuel, GeoCache, Search
from trovabenzina.db.repositories import (
    broadcast_repository,
    fuel_repository,
    geocache_repository,
    language_repository,
    search_repository,
    stats_repository,
    user_repository,
)


class UserRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_upsert_user_resolves_foreign_keys_and_commits(self):
        fake_session = FakeSession(
            execute_results=[
                FakeResult(scalar_one=10),
                FakeResult(scalar_one=20),
                FakeResult(),
            ]
        )
        factory = FakeSessionFactory(fake_session)

        with patch.object(user_repository, "AsyncSession", factory):
            await user_repository.upsert_user(123, "tester", "1", "en")

        self.assertEqual(fake_session.commit_count, 1)
        self.assertEqual(len(fake_session.execute_calls), 3)
        self.assertEqual(fake_session.execute_calls[-1].table.name, "users")

    async def test_upsert_user_skips_language_lookup_when_not_provided(self):
        fake_session = FakeSession(execute_results=[FakeResult(scalar_one=10), FakeResult()])
        factory = FakeSessionFactory(fake_session)

        with patch.object(user_repository, "AsyncSession", factory):
            await user_repository.upsert_user(123, "tester", "1", None)

        self.assertEqual(fake_session.commit_count, 1)
        self.assertEqual(len(fake_session.execute_calls), 2)

    async def test_user_read_helpers(self):
        get_user_session = FakeSession(execute_results=[FakeResult(first=("1", "en"))])
        get_none_session = FakeSession(execute_results=[FakeResult(first=None)])
        fuel_session = FakeSession(execute_results=[FakeResult(scalar_one="2")])
        lang_session = FakeSession(execute_results=[FakeResult(scalar_one_or_none=None)])
        user_id_session = FakeSession(execute_results=[FakeResult(scalar_one_or_none=77)])
        search_users_session = FakeSession(execute_results=[FakeResult(rows=[(100, 1), (200, 2)])])

        with patch.object(user_repository, "AsyncSession", FakeSessionFactory(get_user_session)):
            self.assertEqual(await user_repository.get_user(123), ("1", "en"))
        with patch.object(user_repository, "AsyncSession", FakeSessionFactory(get_none_session)):
            self.assertIsNone(await user_repository.get_user(999))
        with patch.object(user_repository, "AsyncSession", FakeSessionFactory(fuel_session)):
            self.assertEqual(await user_repository.get_user_fuel_code_by_tg_id(123), "2")
        with patch.object(user_repository, "AsyncSession", FakeSessionFactory(lang_session)):
            self.assertEqual(await user_repository.get_user_language_code_by_tg_id(123), DEFAULT_LANGUAGE)
        with patch.object(user_repository, "AsyncSession", FakeSessionFactory(user_id_session)):
            self.assertEqual(await user_repository.get_user_id_by_tg_id(123), 77)
        with patch.object(user_repository, "AsyncSession", FakeSessionFactory(search_users_session)):
            self.assertEqual(await user_repository.get_search_users(), [(100, 1), (200, 2)])


class FuelAndLanguageRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_fuel_repository_helpers_cover_blank_and_non_blank_inputs(self):
        fuel_a = Fuel(id=1, code="1", name="gasoline", uom="liter", avg_consumption_per_100km=Decimal("7.0"))
        fuel_b = Fuel(id=2, code="2", name="diesel", uom="liter", avg_consumption_per_100km=Decimal("5.0"))

        with patch.object(
                fuel_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalars=[fuel_a, fuel_b])])),
        ):
            self.assertEqual(await fuel_repository.get_fuel_map(), {"gasoline": "1", "diesel": "2"})

        with patch.object(
                fuel_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalars=[fuel_a])])),
        ):
            self.assertEqual(await fuel_repository.get_fuels_by_ids_map([1, 1]), {1: fuel_a})

        self.assertIsNone(await fuel_repository.get_fuel_by_code(" "))
        with patch.object(
                fuel_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalars=[fuel_a])])),
        ):
            self.assertEqual(await fuel_repository.get_fuel_by_code("1"), fuel_a)

        self.assertIsNone(await fuel_repository.get_fuel_name_by_code(""))
        with patch.object(
                fuel_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalar_one_or_none="gasoline")])),
        ):
            self.assertEqual(await fuel_repository.get_fuel_name_by_code("1"), "gasoline")

        self.assertEqual(await fuel_repository.get_fuels_by_codes_map([]), {})
        with patch.object(
                fuel_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalars=[fuel_a, fuel_b])])),
        ):
            self.assertEqual(
                await fuel_repository.get_fuels_by_codes_map(["1", "2", "1"]),
                {"1": fuel_a, "2": fuel_b},
            )

        self.assertIsNone(await fuel_repository.get_uom_by_code(""))
        with patch.object(
                fuel_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalar_one_or_none="kg")])),
        ):
            self.assertEqual(await fuel_repository.get_uom_by_code("3"), "kg")

        self.assertEqual(await fuel_repository.get_uom_map_by_codes([]), {})
        with patch.object(
                fuel_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(rows=[("1", "liter"), ("3", "kg")])])),
        ):
            self.assertEqual(
                await fuel_repository.get_uom_map_by_codes(["1", "3", "3"]),
                {"1": "liter", "3": "kg"},
            )

    async def test_language_repository_helpers(self):
        language_row = SimpleNamespace(name="Italiano", code="it")

        with patch.object(
                language_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalars=[language_row])])),
        ):
            self.assertEqual(await language_repository.get_language_map(), {"Italiano": "it"})

        with patch.object(
                language_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalar_one=10)])),
        ):
            self.assertEqual(await language_repository.get_language_id_by_code("it"), 10)


class SearchAndStatsRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_save_search_resolves_ids_adds_row_and_commits(self):
        fake_session = FakeSession(execute_results=[FakeResult(scalar_one=11), FakeResult(scalar_one=22)])
        factory = FakeSessionFactory(fake_session)

        with patch.object(search_repository, "AsyncSession", factory):
            await search_repository.save_search(100, "1", 5.0, 8, 1.8, 1.7)

        self.assertEqual(fake_session.commit_count, 1)
        self.assertEqual(len(fake_session.added), 1)
        created = fake_session.added[0]
        self.assertIsInstance(created, Search)
        self.assertEqual(created.user_id, 11)
        self.assertEqual(created.fuel_id, 22)
        self.assertEqual(created.search_type, "zone")
        self.assertEqual(created.radius, 5.0)
        self.assertEqual(created.num_stations, 8)

    async def test_save_search_accepts_route_searches_without_radius(self):
        fake_session = FakeSession(execute_results=[FakeResult(scalar_one=11), FakeResult(scalar_one=22)])
        factory = FakeSessionFactory(fake_session)

        with patch.object(search_repository, "AsyncSession", factory):
            await search_repository.save_search(100, "1", None, 3, 1.72, 1.71, search_type="route")

        created = fake_session.added[0]
        self.assertEqual(created.search_type, "route")
        self.assertIsNone(created.radius)
        self.assertEqual(created.num_stations, 3)

    async def test_soft_delete_search_helpers(self):
        delete_session = FakeSession(execute_results=[FakeResult(rowcount=4)])
        with patch.object(search_repository, "AsyncSession", FakeSessionFactory(delete_session)):
            self.assertEqual(await search_repository.soft_delete_user_searches(10), 4)
        self.assertEqual(delete_session.commit_count, 1)

        with patch.object(search_repository, "AsyncSession",
                          FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalar_one=10)]))):
            with patch.object(search_repository, "soft_delete_user_searches",
                              new=AsyncMock(return_value=3)) as soft_delete:
                self.assertEqual(await search_repository.soft_delete_user_searches_by_tg_id(123), 3)
        soft_delete.assert_awaited_once_with(10)

    async def test_stats_repository_helpers(self):
        with patch.object(
                stats_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalar_one_or_none=None)])),
        ):
            self.assertEqual(await stats_repository.count_geocoding_month_calls(), 0)

        mappings = [{"fuel_id": 1, "num_searches": 2}, {"fuel_id": 2, "num_searches": 4}]
        with patch.object(
                stats_repository,
                "AsyncSession",
                FakeSessionFactory(
                    FakeSession(execute_results=[FakeResult(scalar_one=44), FakeResult(mappings=mappings)])),
        ):
            self.assertEqual(await stats_repository.get_user_stats(123), mappings)


class GeocacheRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_geocache_save_geocache_and_delete_old_entries(self):
        cache_row = GeoCache(address="Via Roma", lat=45.1, lng=9.2)

        with patch.object(
                geocache_repository,
                "AsyncSession",
                FakeSessionFactory(FakeSession(execute_results=[FakeResult(scalar_one_or_none=cache_row)])),
        ):
            self.assertEqual(await geocache_repository.get_geocache("Via Roma"), cache_row)

        update_session = FakeSession(execute_results=[FakeResult(scalar_one_or_none=cache_row)])
        with patch.object(geocache_repository, "AsyncSession", FakeSessionFactory(update_session)):
            await geocache_repository.save_geocache("Via Roma", 44.4, 10.1)
        self.assertEqual(update_session.commit_count, 1)
        self.assertEqual((cache_row.lat, cache_row.lng), (44.4, 10.1))

        insert_session = FakeSession(execute_results=[FakeResult(scalar_one_or_none=None)])
        with patch.object(geocache_repository, "AsyncSession", FakeSessionFactory(insert_session)):
            await geocache_repository.save_geocache("Via Milano", 45.4, 9.1)
        self.assertEqual(insert_session.commit_count, 1)
        self.assertEqual(len(insert_session.added), 1)
        self.assertEqual(insert_session.added[0].address, "Via Milano")

        delete_session = FakeSession(execute_results=[FakeResult()])
        with patch.object(geocache_repository, "AsyncSession", FakeSessionFactory(delete_session)):
            await geocache_repository.delete_old_geocache(30)
        self.assertEqual(delete_session.commit_count, 1)


class BroadcastRepositoryTests(unittest.IsolatedAsyncioTestCase):
    def test_compact_error_normalizes_and_limits_text(self):
        self.assertIsNone(broadcast_repository._compact_error(None))
        compacted = broadcast_repository._compact_error(" line 1 \n  line 2 ")
        self.assertEqual(compacted, "line 1 line 2")
        self.assertEqual(
            len(broadcast_repository._compact_error("x" * (broadcast_repository.MAX_ERROR_LENGTH + 5))),
            broadcast_repository.MAX_ERROR_LENGTH,
        )

    async def test_claim_pending_broadcasts_returns_rows_and_marks_processing(self):
        broadcasts = [
            BroadcastMessage(id=1, language_code="it", message_text="One"),
            BroadcastMessage(id=2, language_code="en", message_text="Two"),
        ]
        fake_session = FakeSession(
            execute_results=[
                FakeResult(scalars=[1, 2]),
                FakeResult(),
                FakeResult(scalars=broadcasts),
            ]
        )

        with patch.object(broadcast_repository, "AsyncSession", FakeSessionFactory(fake_session)):
            claimed = await broadcast_repository.claim_pending_broadcasts(limit=2)

        self.assertEqual(claimed, broadcasts)
        self.assertEqual(fake_session.begin_count, 1)
        self.assertEqual(len(fake_session.execute_calls), 3)

    async def test_claim_pending_broadcasts_returns_empty_when_no_rows(self):
        fake_session = FakeSession(execute_results=[FakeResult(scalars=[])])

        with patch.object(broadcast_repository, "AsyncSession", FakeSessionFactory(fake_session)):
            claimed = await broadcast_repository.claim_pending_broadcasts()

        self.assertEqual(claimed, [])
        self.assertEqual(len(fake_session.execute_calls), 1)

    async def test_get_broadcast_recipient_tg_ids_for_default_and_specific_languages(self):
        default_session = FakeSession(execute_results=[FakeResult(scalars=[10, 20])])
        other_session = FakeSession(execute_results=[FakeResult(scalars=[30])])

        with patch.object(broadcast_repository, "AsyncSession", FakeSessionFactory(default_session)):
            self.assertEqual(
                await broadcast_repository.get_broadcast_recipient_tg_ids(DEFAULT_LANGUAGE),
                [10, 20],
            )
        with patch.object(broadcast_repository, "AsyncSession", FakeSessionFactory(other_session)):
            self.assertEqual(await broadcast_repository.get_broadcast_recipient_tg_ids("en"), [30])
        self.assertEqual(await broadcast_repository.get_broadcast_recipient_tg_ids(""), [])

    async def test_finalize_broadcast_message_sets_terminal_status_and_commits(self):
        sent_session = FakeSession(execute_results=[FakeResult()])
        with patch.object(broadcast_repository, "AsyncSession", FakeSessionFactory(sent_session)):
            await broadcast_repository.finalize_broadcast_message(
                1,
                10,
                10,
                0,
                last_error=" minor \n issue ",
            )
        self.assertEqual(sent_session.commit_count, 1)

        failed_session = FakeSession(execute_results=[FakeResult()])
        with patch.object(broadcast_repository, "AsyncSession", FakeSessionFactory(failed_session)):
            await broadcast_repository.finalize_broadcast_message(
                2,
                10,
                3,
                7,
                fatal_error=" fatal \n issue ",
            )
        self.assertEqual(failed_session.commit_count, 1)


if __name__ == "__main__":
    unittest.main()
