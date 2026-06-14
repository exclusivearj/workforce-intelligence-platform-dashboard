"""Postgres-backed cache for pre-computed dashboard query results.

Avoids paying Trino cold-query latency on every page load. Cache keys are
deterministic functions of (page, filters) so identical views share an entry.
"""

from __future__ import annotations

import hashlib
import json


def build_cache_key(page: str, filters: dict) -> str:
    """Build a deterministic cache key from page + filter values."""
    normalized = json.dumps(filters, sort_keys=True, default=str)
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:16]
    return f"{page}_{digest}"


def get_cached(conn, cache_key: str):
    """Return a cached DataFrame, or None if missing/expired."""
    import pandas as pd

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT data_json
            FROM dashboard.cache
            WHERE cache_key = %s
              AND (expires_at IS NULL OR expires_at > NOW())
            """,
            (cache_key,),
        )
        row = cur.fetchone()
    if not row:
        return None
    payload = row[0]
    if isinstance(payload, str):
        payload = json.loads(payload)
    return pd.DataFrame(payload)


def set_cached(conn, cache_key: str, df, ttl_hours: int = 24) -> None:
    """Serialise a DataFrame to JSON and upsert it into dashboard.cache."""
    records = df.to_dict(orient="records")
    payload = json.dumps(records, default=str)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO dashboard.cache (cache_key, data_json, row_count, expires_at)
            VALUES (%s, %s::jsonb, %s, NOW() + (%s || ' hours')::interval)
            ON CONFLICT (cache_key) DO UPDATE
                SET data_json = EXCLUDED.data_json,
                    row_count = EXCLUDED.row_count,
                    computed_at = NOW(),
                    expires_at = EXCLUDED.expires_at
            """,
            (cache_key, payload, len(records), ttl_hours),
        )
    conn.commit()
