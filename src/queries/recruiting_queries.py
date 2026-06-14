"""Trino queries for the Recruiting page (postgresql.analytics.rpt_recruiting_funnel)."""

from __future__ import annotations

from src.queries import run_query

_TABLE = "postgresql.analytics.rpt_recruiting_funnel"
_STAGE_ORDER = ["applied", "phone_screen", "interview", "offer", "hired"]


def get_funnel_summary(
    department: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    clauses = []
    if department:
        clauses.append(f"department = '{department}'")
    if start_date:
        clauses.append(f"year_month >= '{start_date}'")
    if end_date:
        clauses.append(f"year_month <= '{end_date}'")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    # Unpivot the funnel counts into ordered (stage, count) rows with conversion.
    sql = f"""
        WITH totals AS (
            SELECT
                SUM(applied_count)      AS applied,
                SUM(phone_screen_count) AS phone_screen,
                SUM(interview_count)    AS interview,
                SUM(offer_count)        AS offer,
                SUM(hired_count)        AS hired
            FROM {_TABLE}
            {where}
        )
        SELECT stage, count,
               ROUND(100.0 * count / NULLIF(MAX(count) OVER (), 0), 1) AS conversion_rate_pct
        FROM totals
        CROSS JOIN UNNEST(
            ARRAY['applied', 'phone_screen', 'interview', 'offer', 'hired'],
            ARRAY[applied, phone_screen, interview, offer, hired]
        ) AS t(stage, count)
    """
    return run_query(sql)


def get_time_to_hire_by_role(department: str | None = None):
    where = f"WHERE department = '{department}'" if department else ""
    sql = f"""
        SELECT job_title, department,
               AVG(application_to_hire_days_avg) AS application_to_hire_days_avg,
               SUM(hired_count) AS hired_count
        FROM {_TABLE}
        {where}
        GROUP BY job_title, department
        ORDER BY application_to_hire_days_avg DESC
    """
    return run_query(sql)


def get_offer_acceptance_rate(department: str | None = None):
    where = f"WHERE department = '{department}'" if department else ""
    sql = f"""
        SELECT department, AVG(offer_acceptance_rate_pct) AS offer_acceptance_rate_pct
        FROM {_TABLE}
        {where}
        GROUP BY department
        ORDER BY offer_acceptance_rate_pct DESC
    """
    return run_query(sql)


def stage_order() -> list[str]:
    return list(_STAGE_ORDER)
