from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable
from unittest.mock import AsyncMock

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",
)
os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-api-key")
os.environ.setdefault("LOG_LEVEL", "INFO")


class FakeScalarSequence:
    def __init__(self, values: Iterable[Any] | None = None):
        self._values = list(values or [])

    def all(self) -> list[Any]:
        return list(self._values)

    def first(self) -> Any:
        return self._values[0] if self._values else None


class FakeMappingsSequence:
    def __init__(self, values: Iterable[dict[str, Any]] | None = None):
        self._values = list(values or [])

    def all(self) -> list[dict[str, Any]]:
        return list(self._values)


class FakeResult:
    _missing = object()

    def __init__(
            self,
            *,
            rows: Iterable[Any] | None = None,
            scalars: Iterable[Any] | None = None,
            mappings: Iterable[dict[str, Any]] | None = None,
            first: Any = _missing,
            scalar_one: Any = _missing,
            scalar_one_or_none: Any = _missing,
            rowcount: int | None = None,
    ):
        self._rows = list(rows or [])
        self._scalars = list(scalars) if scalars is not None else None
        self._mappings = list(mappings) if mappings is not None else None
        self._first = first
        self._scalar_one = scalar_one
        self._scalar_one_or_none = scalar_one_or_none
        self.rowcount = rowcount

    def first(self) -> Any:
        if self._first is not self._missing:
            return self._first
        return self._rows[0] if self._rows else None

    def all(self) -> list[Any]:
        return list(self._rows)

    def scalars(self) -> FakeScalarSequence:
        return FakeScalarSequence(self._rows if self._scalars is None else self._scalars)

    def scalar_one(self) -> Any:
        if self._scalar_one is not self._missing:
            return self._scalar_one
        values = self._rows if self._scalars is None else self._scalars
        if not values:
            raise AssertionError("FakeResult.scalar_one() has no value configured")
        return values[0]

    def scalar_one_or_none(self) -> Any:
        if self._scalar_one_or_none is not self._missing:
            return self._scalar_one_or_none
        values = self._rows if self._scalars is None else self._scalars
        return values[0] if values else None

    def mappings(self) -> FakeMappingsSequence:
        values = self._rows if self._mappings is None else self._mappings
        return FakeMappingsSequence(values)


class FakeTransaction:
    async def __aenter__(self) -> "FakeTransaction":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class FakeSession:
    def __init__(self, execute_results: Iterable[Any] | None = None):
        self.execute_results = list(execute_results or [])
        self.execute_calls: list[Any] = []
        self.added: list[Any] = []
        self.commit_count = 0
        self.begin_count = 0

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    def begin(self) -> FakeTransaction:
        self.begin_count += 1
        return FakeTransaction()

    async def execute(self, statement: Any) -> Any:
        self.execute_calls.append(statement)
        if not self.execute_results:
            return FakeResult()
        result = self.execute_results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def add(self, instance: Any) -> None:
        self.added.append(instance)

    async def commit(self) -> None:
        self.commit_count += 1


class FakeSessionFactory:
    def __init__(self, *sessions: FakeSession):
        self._sessions = list(sessions)
        self.created: list[FakeSession] = []

    def __call__(self) -> FakeSession:
        if not self._sessions:
            raise AssertionError("No fake sessions left")
        session = self._sessions.pop(0)
        self.created.append(session)
        return session


class FakeHTTPResponse:
    def __init__(self, *, status: int = 200, json_data: Any = None, json_exc: Exception | None = None):
        self.status = status
        self._json_data = json_data
        self._json_exc = json_exc

    async def __aenter__(self) -> "FakeHTTPResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def json(self, *args, **kwargs) -> Any:
        if self._json_exc:
            raise self._json_exc
        return self._json_data


class FakeHTTPSession:
    def __init__(
            self,
            *,
            get_response: FakeHTTPResponse | None = None,
            post_response: FakeHTTPResponse | None = None,
            get_exc: Exception | None = None,
            post_exc: Exception | None = None,
    ):
        self.get_response = get_response or FakeHTTPResponse()
        self.post_response = post_response or FakeHTTPResponse()
        self.get_exc = get_exc
        self.post_exc = post_exc
        self.get_calls: list[tuple[str, dict[str, Any]]] = []
        self.post_calls: list[tuple[str, dict[str, Any]]] = []

    async def __aenter__(self) -> "FakeHTTPSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    def get(self, url: str, **kwargs) -> FakeHTTPResponse:
        self.get_calls.append((url, kwargs))
        if self.get_exc:
            raise self.get_exc
        return self.get_response

    def post(self, url: str, **kwargs) -> FakeHTTPResponse:
        self.post_calls.append((url, kwargs))
        if self.post_exc:
            raise self.post_exc
        return self.post_response


def make_sent_message(chat_id: int = 100, message_id: int = 999) -> SimpleNamespace:
    return SimpleNamespace(chat_id=chat_id, message_id=message_id)


def make_message(
        *,
        text: str | None = None,
        chat_id: int = 100,
        location: Any = None,
        reply_message: Any | None = None,
) -> SimpleNamespace:
    sent_message = reply_message or make_sent_message(chat_id=chat_id, message_id=999)
    return SimpleNamespace(
        text=text,
        chat=SimpleNamespace(id=chat_id),
        chat_id=chat_id,
        message_id=getattr(sent_message, "message_id", 999),
        location=location,
        reply_text=AsyncMock(return_value=sent_message),
        reply_html=AsyncMock(return_value=sent_message),
    )


def make_message_update(
        *,
        text: str | None = None,
        user_id: int = 1,
        username: str = "tester",
        chat_id: int = 100,
        location: Any = None,
        reply_message: Any | None = None,
) -> SimpleNamespace:
    message = make_message(text=text, chat_id=chat_id, location=location, reply_message=reply_message)
    return SimpleNamespace(
        message=message,
        callback_query=None,
        effective_message=message,
        effective_user=SimpleNamespace(id=user_id, username=username),
        effective_chat=SimpleNamespace(id=chat_id),
    )


def make_callback_update(
        *,
        data: str,
        user_id: int = 1,
        username: str = "tester",
        chat_id: int = 100,
        reply_message: Any | None = None,
        edited_message: Any | None = None,
) -> SimpleNamespace:
    source_message = make_message(chat_id=chat_id, reply_message=reply_message)
    edited = edited_message or make_sent_message(chat_id=chat_id, message_id=1001)
    callback_query = SimpleNamespace(
        data=data,
        message=source_message,
        answer=AsyncMock(),
        edit_message_text=AsyncMock(return_value=edited),
        edit_message_reply_markup=AsyncMock(),
    )
    return SimpleNamespace(
        message=None,
        callback_query=callback_query,
        effective_message=source_message,
        effective_user=SimpleNamespace(id=user_id, username=username),
        effective_chat=SimpleNamespace(id=chat_id),
    )


def make_context(
        *,
        bot: Any | None = None,
        application: Any | None = None,
        user_data: dict[str, Any] | None = None,
        chat_data: dict[str, Any] | None = None,
) -> SimpleNamespace:
    bot_obj = bot or SimpleNamespace(
        delete_message=AsyncMock(),
        send_message=AsyncMock(),
    )
    application_obj = application or SimpleNamespace(bot=bot_obj)
    return SimpleNamespace(
        bot=bot_obj,
        application=application_obj,
        user_data={} if user_data is None else user_data,
        chat_data={} if chat_data is None else chat_data,
    )


def keyboard_layout(markup: Any) -> list[list[tuple[str, str]]]:
    return [
        [(button.text, button.callback_data) for button in row]
        for row in markup.inline_keyboard
    ]
