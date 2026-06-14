"""Tests for Trino query builders (run_query mocked)."""

from __future__ import annotations

import pandas as pd

from src.queries import attrition_queries, headcount_queries, recruiting_queries


def _capture(monkeypatch, module, return_df):
    captured = {}

    def fake_run_query(sql, params=None):
        captured["sql"] = sql
        return return_df

    monkeypatch.setattr(module, "run_query", fake_run_query)
    return captured


def test_headcount_trend_columns_and_catalog(monkeypatch):
    df = pd.DataFrame({"date": ["2024-01-01"], "department": ["Data"], "level": ["IC3"], "headcount": [5]})
    captured = _capture(monkeypatch, headcount_queries, df)
    out = headcount_queries.get_headcount_trend(department="Data")
    assert list(out.columns) == ["date", "department", "level", "headcount"]
    assert "postgresql.analytics.fct_headcount_daily" in captured["sql"]
    assert "department = 'Data'" in captured["sql"]


def test_headcount_no_filters_has_no_where(monkeypatch):
    captured = _capture(monkeypatch, headcount_queries, pd.DataFrame())
    headcount_queries.get_headcount_trend()
    assert "WHERE" not in captured["sql"]


def test_attrition_trend_catalog(monkeypatch):
    captured = _capture(monkeypatch, attrition_queries, pd.DataFrame())
    attrition_queries.get_attrition_trend(department="Engineering")
    assert "postgresql.analytics.fct_attrition_monthly" in captured["sql"]
    assert "department = 'Engineering'" in captured["sql"]


def test_funnel_summary_stage_order(monkeypatch):
    stages = ["applied", "phone_screen", "interview", "offer", "hired"]
    df = pd.DataFrame({"stage": stages, "count": [100, 60, 40, 14, 6], "conversion_rate_pct": [100, 60, 40, 14, 6]})
    captured = _capture(monkeypatch, recruiting_queries, df)
    out = recruiting_queries.get_funnel_summary()
    assert list(out["stage"]) == stages
    assert "postgresql.analytics.rpt_recruiting_funnel" in captured["sql"]


def test_no_raw_table_names(monkeypatch):
    """Query SQL must always use the Trino catalog prefix, never bare schema names."""
    for module, fn in (
        (headcount_queries, headcount_queries.get_headcount_trend),
        (attrition_queries, attrition_queries.get_attrition_trend),
        (recruiting_queries, recruiting_queries.get_funnel_summary),
    ):
        captured = _capture(monkeypatch, module, pd.DataFrame())
        fn()
        assert "postgresql.analytics." in captured["sql"]
        assert "FROM analytics." not in captured["sql"]
