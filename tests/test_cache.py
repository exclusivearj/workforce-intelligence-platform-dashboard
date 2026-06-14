"""Tests for the Postgres-backed dashboard cache."""

from __future__ import annotations

import pandas as pd

from tests.conftest import FakeConn, RoundTripConn

from src.components.cache import build_cache_key, get_cached, set_cached


def test_build_cache_key_deterministic():
    f = {"departments": ["Data"], "levels": ["IC3"]}
    assert build_cache_key("headcount", f) == build_cache_key("headcount", f)


def test_build_cache_key_order_independent():
    a = build_cache_key("headcount", {"departments": ["Data"], "levels": ["IC3"]})
    b = build_cache_key("headcount", {"levels": ["IC3"], "departments": ["Data"]})
    assert a == b


def test_build_cache_key_varies_by_page():
    f = {"departments": ["Data"]}
    assert build_cache_key("headcount", f) != build_cache_key("attrition", f)


def test_set_then_get_round_trip():
    conn = RoundTripConn()
    df = pd.DataFrame({"department": ["Data", "Eng"], "headcount": [5, 9]})
    key = build_cache_key("headcount", {"departments": []})
    set_cached(conn, key, df)
    assert conn.committed
    out = get_cached(conn, key)
    pd.testing.assert_frame_equal(out, df)


def test_get_cached_miss_returns_none():
    conn = FakeConn(fetchone_queue=[None])
    assert get_cached(conn, "missing") is None
