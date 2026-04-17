from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

try:
    from tests.support import FakeHTTPResponse, FakeHTTPSession
except ModuleNotFoundError:
    from support import FakeHTTPResponse, FakeHTTPSession

from trovabenzina.api.googlemaps import geocoding
from trovabenzina.api.mise import station_detail, stations_search


class GeocodingTests(unittest.IsolatedAsyncioTestCase):
    async def test_geocode_address_returns_cached_coordinates(self):
        with (
            patch.object(geocoding, "get_geocache", new=AsyncMock(return_value=SimpleNamespace(lat=45.1, lng=9.2))),
            patch.object(geocoding.aiohttp, "ClientSession") as client_session,
        ):
            coords = await geocoding.geocode_address("Milano")

        self.assertEqual(coords, (45.1, 9.2))
        client_session.assert_not_called()

    async def test_geocode_address_stops_when_cap_is_reached(self):
        with (
            patch.object(geocoding, "get_geocache", new=AsyncMock(return_value=None)),
            patch.object(geocoding, "count_geocoding_month_calls",
                         new=AsyncMock(return_value=geocoding.GEOCODE_HARD_CAP)),
            patch.object(geocoding.aiohttp, "ClientSession") as client_session,
        ):
            coords = await geocoding.geocode_address("Roma")

        self.assertIsNone(coords)
        client_session.assert_not_called()

    async def test_geocode_address_uses_best_result_and_updates_cache(self):
        payload = {
            "results": [
                {
                    "partial_match": True,
                    "address_components": [{"types": ["locality"], "short_name": "Roma"}],
                    "geometry": {
                        "location_type": "ROOFTOP",
                        "location": {"lat": 40.0, "lng": 11.0},
                    },
                },
                {
                    "partial_match": False,
                    "address_components": [{"types": ["locality"], "short_name": "Milano"}],
                    "geometry": {
                        "location_type": "GEOMETRIC_CENTER",
                        "location": {"lat": 45.4642, "lng": 9.19},
                    },
                },
            ]
        }
        session = FakeHTTPSession(get_response=FakeHTTPResponse(status=200, json_data=payload))

        with (
            patch.object(geocoding, "get_geocache", new=AsyncMock(return_value=None)),
            patch.object(geocoding, "count_geocoding_month_calls", new=AsyncMock(return_value=0)),
            patch.object(geocoding, "save_geocache", new=AsyncMock()) as save_geocache,
            patch.object(geocoding.aiohttp, "ClientSession", Mock(return_value=session)),
        ):
            coords = await geocoding.geocode_address("Milano")

        self.assertEqual(coords, (45.4642, 9.19))
        self.assertEqual(session.get_calls[0][1]["params"]["components"], "country:IT")
        save_geocache.assert_awaited_once_with("Milano", 45.4642, 9.19)

    async def test_geocode_address_returns_none_for_invalid_payload(self):
        invalid_payloads = [
            {"results": []},
            {
                "results": [
                    {
                        "address_components": [{"types": ["country"], "short_name": "IT"}],
                        "geometry": {"location_type": "ROOFTOP", "location": {"lat": 1, "lng": 2}},
                    }
                ]
            },
            {
                "results": [
                    {
                        "address_components": [{"types": ["locality"], "short_name": "IT"}],
                        "geometry": {"location_type": "APPROXIMATE", "location": {"lat": 1, "lng": 2}},
                    }
                ]
            },
            {
                "results": [
                    {
                        "address_components": [{"types": ["locality"], "short_name": "IT"}],
                        "geometry": {"location_type": "ROOFTOP", "location": {"lat": 1}},
                    }
                ]
            },
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                session = FakeHTTPSession(get_response=FakeHTTPResponse(status=200, json_data=payload))
                with (
                    patch.object(geocoding, "get_geocache", new=AsyncMock(return_value=None)),
                    patch.object(geocoding, "count_geocoding_month_calls", new=AsyncMock(return_value=0)),
                    patch.object(geocoding.aiohttp, "ClientSession", Mock(return_value=session)),
                ):
                    coords = await geocoding.geocode_address("Bad address")
                self.assertIsNone(coords)

    async def test_geocode_address_handles_http_errors_and_exceptions(self):
        bad_status_session = FakeHTTPSession(get_response=FakeHTTPResponse(status=500, json_data={}))
        with (
            patch.object(geocoding, "get_geocache", new=AsyncMock(return_value=None)),
            patch.object(geocoding, "count_geocoding_month_calls", new=AsyncMock(return_value=0)),
            patch.object(geocoding.aiohttp, "ClientSession", Mock(return_value=bad_status_session)),
        ):
            self.assertIsNone(await geocoding.geocode_address("Server error"))

        broken_session = FakeHTTPSession(get_exc=RuntimeError("network"))
        with (
            patch.object(geocoding, "get_geocache", new=AsyncMock(return_value=None)),
            patch.object(geocoding, "count_geocoding_month_calls", new=AsyncMock(return_value=0)),
            patch.object(geocoding.aiohttp, "ClientSession", Mock(return_value=broken_session)),
        ):
            self.assertIsNone(await geocoding.geocode_address("Network error"))

    async def test_geocode_address_with_country_uses_cache_and_marks_italy(self):
        with (
            patch.object(geocoding, "get_geocache", new=AsyncMock(return_value=SimpleNamespace(lat=41.9, lng=12.5))),
            patch.object(geocoding.aiohttp, "ClientSession") as client_session,
        ):
            coords = await geocoding.geocode_address_with_country("Roma")

        self.assertEqual(coords, (41.9, 12.5, "IT"))
        client_session.assert_not_called()

    async def test_geocode_address_with_country_caches_only_italian_results(self):
        italy_payload = {
            "results": [
                {
                    "address_components": [{"types": ["country"], "short_name": "IT"}],
                    "geometry": {"location": {"lat": 44.5, "lng": 11.3}},
                }
            ]
        }
        foreign_payload = {
            "results": [
                {
                    "address_components": [{"types": ["country"], "short_name": "FR"}],
                    "geometry": {"location": {"lat": 48.8, "lng": 2.3}},
                }
            ]
        }

        for payload, expected, should_cache in (
                (italy_payload, (44.5, 11.3, "IT"), True),
                (foreign_payload, (48.8, 2.3, "FR"), False),
        ):
            with self.subTest(expected=expected):
                session = FakeHTTPSession(get_response=FakeHTTPResponse(status=200, json_data=payload))
                with (
                    patch.object(geocoding, "get_geocache", new=AsyncMock(return_value=None)),
                    patch.object(geocoding, "count_geocoding_month_calls", new=AsyncMock(return_value=0)),
                    patch.object(geocoding, "save_geocache", new=AsyncMock()) as save_geocache,
                    patch.object(geocoding.aiohttp, "ClientSession", Mock(return_value=session)),
                ):
                    coords = await geocoding.geocode_address_with_country("Address")

                self.assertEqual(coords, expected)
                if should_cache:
                    save_geocache.assert_awaited_once()
                else:
                    save_geocache.assert_not_awaited()

    async def test_geocode_address_with_country_returns_none_for_invalid_http_payload(self):
        session = FakeHTTPSession(get_response=FakeHTTPResponse(status=200, json_data={"results": []}))
        with (
            patch.object(geocoding, "get_geocache", new=AsyncMock(return_value=None)),
            patch.object(geocoding, "count_geocoding_month_calls", new=AsyncMock(return_value=0)),
            patch.object(geocoding.aiohttp, "ClientSession", Mock(return_value=session)),
        ):
            self.assertIsNone(await geocoding.geocode_address_with_country("Empty"))

        session = FakeHTTPSession(get_response=FakeHTTPResponse(status=500, json_data={}))
        with (
            patch.object(geocoding, "get_geocache", new=AsyncMock(return_value=None)),
            patch.object(geocoding, "count_geocoding_month_calls", new=AsyncMock(return_value=0)),
            patch.object(geocoding.aiohttp, "ClientSession", Mock(return_value=session)),
        ):
            self.assertIsNone(await geocoding.geocode_address_with_country("Error"))


class MiseSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_stations_returns_payload_and_sends_expected_json(self):
        session = FakeHTTPSession(
            post_response=FakeHTTPResponse(status=200, json_data={"results": [{"id": 1}]})
        )
        with patch.object(stations_search.aiohttp, "ClientSession", Mock(return_value=session)):
            payload = await stations_search.search_stations(45.0, 9.0, 5.0, "1-x")

        self.assertEqual(payload, {"results": [{"id": 1}]})
        self.assertEqual(
            session.post_calls[0][1]["json"],
            {
                "points": [{"lat": 45.0, "lng": 9.0}],
                "radius": 5.0,
                "fuelType": "1-x",
                "priceOrder": "asc",
            },
        )

    async def test_search_route_stations_returns_payload_and_sends_expected_json(self):
        session = FakeHTTPSession(
            post_response=FakeHTTPResponse(status=200, json_data={"results": [{"id": 2}]})
        )
        with patch.object(stations_search.aiohttp, "ClientSession", Mock(return_value=session)):
            payload = await stations_search.search_route_stations(45.0, 9.0, 44.5, 11.3, "1-x")

        self.assertEqual(payload, {"results": [{"id": 2}]})
        self.assertEqual(
            session.post_calls[0][1]["json"],
            {
                "points": [{"lat": 45.0, "lng": 9.0}, {"lat": 44.5, "lng": 11.3}],
                "fuelType": "1-x",
                "priceOrder": "asc",
            },
        )

    async def test_search_clients_return_none_for_invalid_response_or_exception(self):
        bad_payload_session = FakeHTTPSession(post_response=FakeHTTPResponse(status=200, json_data={"oops": []}))
        with patch.object(stations_search.aiohttp, "ClientSession", Mock(return_value=bad_payload_session)):
            self.assertIsNone(await stations_search.search_stations(1, 2, 3, "fuel"))
        with patch.object(stations_search.aiohttp, "ClientSession", Mock(return_value=bad_payload_session)):
            self.assertIsNone(await stations_search.search_route_stations(1, 2, 3, 4, "fuel"))

        bad_status_session = FakeHTTPSession(post_response=FakeHTTPResponse(status=503, json_data={}))
        with patch.object(stations_search.aiohttp, "ClientSession", Mock(return_value=bad_status_session)):
            self.assertIsNone(await stations_search.search_stations(1, 2, 3, "fuel"))
        with patch.object(stations_search.aiohttp, "ClientSession", Mock(return_value=bad_status_session)):
            self.assertIsNone(await stations_search.search_route_stations(1, 2, 3, 4, "fuel"))

        broken_session = FakeHTTPSession(post_exc=RuntimeError("down"))
        with patch.object(stations_search.aiohttp, "ClientSession", Mock(return_value=broken_session)):
            self.assertIsNone(await stations_search.search_stations(1, 2, 3, "fuel"))
        with patch.object(stations_search.aiohttp, "ClientSession", Mock(return_value=broken_session)):
            self.assertIsNone(await stations_search.search_route_stations(1, 2, 3, 4, "fuel"))


class MiseDetailTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_station_address_returns_address(self):
        session = FakeHTTPSession(get_response=FakeHTTPResponse(status=200, json_data={"address": "Via Roma 1"}))
        with patch.object(station_detail.aiohttp, "ClientSession", Mock(return_value=session)):
            address = await station_detail.get_station_address(123)

        self.assertEqual(address, "Via Roma 1")
        self.assertEqual(session.get_calls[0][0], station_detail.MISE_DETAIL_URL.format(id=123))

    async def test_get_station_address_returns_none_for_bad_status_invalid_payload_or_exception(self):
        bad_status_session = FakeHTTPSession(get_response=FakeHTTPResponse(status=404, json_data={}))
        with patch.object(station_detail.aiohttp, "ClientSession", Mock(return_value=bad_status_session)):
            self.assertIsNone(await station_detail.get_station_address(1))

        invalid_payload_session = FakeHTTPSession(
            get_response=FakeHTTPResponse(status=200, json_data=["not", "a", "dict"]))
        with patch.object(station_detail.aiohttp, "ClientSession", Mock(return_value=invalid_payload_session)):
            self.assertIsNone(await station_detail.get_station_address(1))

        broken_session = FakeHTTPSession(get_exc=RuntimeError("boom"))
        with patch.object(station_detail.aiohttp, "ClientSession", Mock(return_value=broken_session)):
            self.assertIsNone(await station_detail.get_station_address(1))


if __name__ == "__main__":
    unittest.main()
