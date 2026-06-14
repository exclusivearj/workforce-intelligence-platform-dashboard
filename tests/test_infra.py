"""Tests for run_query, db connection, alerts, and remaining query builders."""

from __future__ import annotations

import sys
import types

import pandas as pd

from src.queries import attrition_queries, headcount_queries, recruiting_queries


def test_run_query_uses_trino_and_returns_dataframe(monkeypatch):
    class _Cursor:
        description = [("date",), ("headcount",)]

        def execute(self, sql, params):
            self.sql = sql

        def fetchall(self):
            return [("2024-01-01", 5)]

    class _Conn:
        def cursor(self):
            return _Cursor()

    trino_mod = types.ModuleType("trino")
    dbapi = types.ModuleType("trino.dbapi")
    dbapi.connect = lambda **kwargs: _Conn()
    trino_mod.dbapi = dbapi
    monkeypatch.setitem(sys.modules, "trino", trino_mod)
    monkeypatch.setitem(sys.modules, "trino.dbapi", dbapi)

    from src.queries import run_query

    df = run_query("SELECT date, headcount FROM postgresql.analytics.fct_headcount_daily")
    assert list(df.columns) == ["date", "headcount"]
    assert len(df) == 1


def test_get_connection_builds_from_env(monkeypatch):
    captured = {}

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return "CONN"

    pkg = types.ModuleType("psycopg2")
    pkg.connect = fake_connect
    monkeypatch.setitem(sys.modules, "psycopg2", pkg)

    from src.utils.db import get_connection

    assert get_connection() == "CONN"
    assert captured["dbname"]


def test_alerts_logs_without_webhook(monkeypatch, caplog):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    from src.utils.alerts import send_slack_alert

    with caplog.at_level("WARNING"):
        assert send_slack_alert("hi") is False


def _capture(monkeypatch, module):
    captured = {}
    monkeypatch.setattr(
        module, "run_query",
        lambda sql, params=None: captured.setdefault("sql", sql) or pd.DataFrame(),
    )
    return captured


def test_headcount_snapshot_and_by_level(monkeypatch):
    captured = _capture(monkeypatch, headcount_queries)
    headcount_queries.get_headcount_snapshot("2024-01-15")
    assert "pct_of_total" in captured["sql"]
    captured2 = _capture(monkeypatch, headcount_queries)
    headcount_queries.get_headcount_by_level("Data")
    assert "department = 'Data'" in captured2["sql"]


def test_attrition_by_dept_and_top(monkeypatch):
    captured = _capture(monkeypatch, attrition_queries)
    attrition_queries.get_attrition_by_department("2024-01")
    assert "year_month = '2024-01'" in captured["sql"]
    captured2 = _capture(monkeypatch, attrition_queries)
    attrition_queries.get_top_attrition_departments(3)
    assert "LIMIT 3" in captured2["sql"]


def test_recruiting_time_to_hire_and_acceptance(monkeypatch):
    captured = _capture(monkeypatch, recruiting_queries)
    recruiting_queries.get_time_to_hire_by_role("Data")
    assert "postgresql.analytics.rpt_recruiting_funnel" in captured["sql"]
    captured2 = _capture(monkeypatch, recruiting_queries)
    recruiting_queries.get_offer_acceptance_rate()
    assert "offer_acceptance_rate_pct" in captured2["sql"]
    assert recruiting_queries.stage_order()[0] == "applied"
