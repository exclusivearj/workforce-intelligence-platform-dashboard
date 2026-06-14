"""dashboard_refresh — pre-compute Trino queries into the Postgres cache daily."""

from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="dashboard_refresh",
    schedule="0 7 * * *",  # daily 07:00, after hr_ingestion (06:00)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["dashboard", "people-analytics"],
)
def dashboard_refresh_dag():
    @task
    def refresh_dashboard_cache() -> dict:
        from src.components.cache import build_cache_key, set_cached
        from src.components.filters import default_filters
        from src.queries.attrition_queries import get_attrition_trend
        from src.queries.headcount_queries import get_headcount_trend
        from src.queries.recruiting_queries import get_funnel_summary
        from src.utils.db import get_connection

        filters = default_filters()
        conn = get_connection()
        keys_refreshed = 0
        total_rows = 0
        try:
            for page, df in (
                ("headcount", get_headcount_trend()),
                ("attrition", get_attrition_trend()),
                ("recruiting", get_funnel_summary()),
            ):
                key = build_cache_key(page, filters)
                set_cached(conn, key, df)
                keys_refreshed += 1
                total_rows += len(df)
        finally:
            conn.close()
        return {"keys_refreshed": keys_refreshed, "total_rows_cached": total_rows}

    @task
    def notify_dashboard_updated(stats: dict) -> None:
        from src.utils.alerts import send_slack_alert

        send_slack_alert(
            f"Dashboard cache refreshed: {stats['keys_refreshed']} keys, "
            f"{stats['total_rows_cached']} rows."
        )

    notify_dashboard_updated(refresh_dashboard_cache())


dashboard_refresh_dag()
