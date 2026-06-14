"""Shared fixtures for the dashboard test suite."""

from __future__ import annotations

import json


class FakeCursor:
    def __init__(self, fetchone_queue=None):
        self.executed: list[tuple] = []
        self._fetchone = list(fetchone_queue or [])

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._fetchone.pop(0) if self._fetchone else None


class FakeConn:
    """In-memory cache store keyed by cache_key for round-trip cache tests."""

    def __init__(self, fetchone_queue=None):
        self._cursor = FakeCursor(fetchone_queue)
        self.committed = False
        self.store: dict[str, str] = {}

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True


class RoundTripCursor:
    """Cursor that emulates the cache upsert + lookup against an in-memory dict."""

    def __init__(self, store: dict):
        self.store = store
        self._last = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if "INSERT INTO dashboard.cache" in sql:
            self.store[params[0]] = params[1]  # cache_key -> json payload
        elif "SELECT data_json" in sql:
            key = params[0]
            self._last = (self.store.get(key),) if key in self.store else None

    def fetchone(self):
        return self._last


class RoundTripConn:
    def __init__(self):
        self.store: dict[str, str] = {}
        self._cursor = RoundTripCursor(self.store)
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True


def loads(payload):
    return json.loads(payload) if isinstance(payload, str) else payload
