"""Trino connection + query execution helpers.

All analytical reads go through Trino's ``postgresql`` catalog (never Postgres
directly) to mirror the production OLAP access pattern. ``trino`` and ``pandas``
are imported lazily so query-builder logic stays unit-testable without them.
"""

from __future__ import annotations

import logging
import os
import time

logger = logging.getLogger(__name__)


def get_trino_connection():
    import trino

    return trino.dbapi.connect(
        host=os.getenv("TRINO_HOST", "localhost"),
        port=int(os.getenv("TRINO_PORT", "8080")),
        user=os.getenv("TRINO_USER", "trino"),
        catalog="postgresql",
        schema="analytics",
    )


def run_query(sql: str, params: dict | None = None):
    """Execute SQL on Trino and return a pandas DataFrame. Logs query time."""
    import pandas as pd

    conn = get_trino_connection()
    start = time.perf_counter()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or {})
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description] if cur.description else []
    finally:
        elapsed = time.perf_counter() - start
        logger.info("Trino query took %.3fs", elapsed)
    return pd.DataFrame(rows, columns=columns)
