"""Trino queries for the Headcount page (postgresql.analytics.fct_headcount_daily)."""

from __future__ import annotations

from src.queries import run_query

_TABLE = "postgresql.analytics.fct_headcount_daily"


def _filters_clause(
    department: str | None,
    level: str | None,
    employment_type: str | None,
    start_date: str | None,
    end_date: str | None,
) -> str:
    clauses = []
    if department:
        clauses.append(f"department = '{department}'")
    if level:
        clauses.append(f"level = '{level}'")
    if employment_type:
        clauses.append(f"employment_type = '{employment_type}'")
    if start_date:
        clauses.append(f"date >= DATE '{start_date}'")
    if end_date:
        clauses.append(f"date <= DATE '{end_date}'")
    return ("WHERE " + " AND ".join(clauses)) if clauses else ""


def get_headcount_trend(
    department: str | None = None,
    level: str | None = None,
    employment_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    where = _filters_clause(department, level, employment_type, start_date, end_date)
    sql = f"""
        SELECT date, department, level, SUM(headcount) AS headcount
        FROM {_TABLE}
        {where}
        GROUP BY date, department, level
        ORDER BY date
    """
    return run_query(sql)


def get_headcount_snapshot(as_of_date: str):
    sql = f"""
        SELECT department, SUM(headcount) AS headcount,
               ROUND(100.0 * SUM(headcount) / SUM(SUM(headcount)) OVER (), 1) AS pct_of_total
        FROM {_TABLE}
        WHERE date = DATE '{as_of_date}'
        GROUP BY department
        ORDER BY headcount DESC
    """
    return run_query(sql)


def get_headcount_by_level(department: str | None = None):
    where = f"AND department = '{department}'" if department else ""
    sql = f"""
        SELECT level, SUM(headcount) AS headcount,
               ROUND(100.0 * SUM(headcount) / SUM(SUM(headcount)) OVER (), 1) AS pct_of_total
        FROM {_TABLE}
        WHERE date = (SELECT MAX(date) FROM {_TABLE}) {where}
        GROUP BY level
        ORDER BY level
    """
    return run_query(sql)
