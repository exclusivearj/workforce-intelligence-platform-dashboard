"""Trino queries for the Attrition page (postgresql.analytics.fct_attrition_monthly)."""

from __future__ import annotations

from src.queries import run_query

_TABLE = "postgresql.analytics.fct_attrition_monthly"


def get_attrition_trend(
    department: str | None = None,
    start_year_month: str | None = None,
    end_year_month: str | None = None,
):
    clauses = []
    if department:
        clauses.append(f"department = '{department}'")
    if start_year_month:
        clauses.append(f"year_month >= '{start_year_month}'")
    if end_year_month:
        clauses.append(f"year_month <= '{end_year_month}'")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        SELECT year_month, department, attrition_rate_pct,
               rolling_12m_attrition_rate_pct
        FROM {_TABLE}
        {where}
        ORDER BY year_month
    """
    return run_query(sql)


def get_attrition_by_department(year_month: str | None = None):
    where = f"WHERE year_month = '{year_month}'" if year_month else ""
    sql = f"""
        SELECT department,
               SUM(voluntary_terminations) AS voluntary_terminations,
               SUM(involuntary_terminations) AS involuntary_terminations,
               SUM(total_terminations) AS total_terminations
        FROM {_TABLE}
        {where}
        GROUP BY department
        ORDER BY total_terminations DESC
    """
    return run_query(sql)


def get_top_attrition_departments(n: int = 5):
    sql = f"""
        SELECT department,
               AVG(rolling_12m_attrition_rate_pct) AS rolling_12m_attrition_rate_pct
        FROM {_TABLE}
        GROUP BY department
        ORDER BY rolling_12m_attrition_rate_pct DESC
        LIMIT {int(n)}
    """
    return run_query(sql)
