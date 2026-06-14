"""Shared filter sidebar component.

The pure helpers (default_filters / normalize_filters) hold all the logic and are
unit-tested without Streamlit; render_filters wires them to the st.sidebar widgets.
"""

from __future__ import annotations

from datetime import date, timedelta

EMPLOYMENT_TYPE_OPTIONS = ["All", "Full-time", "Part-time", "Contractor"]
_EMPLOYMENT_TYPE_MAP = {
    "All": None,
    "Full-time": "full_time",
    "Part-time": "part_time",
    "Contractor": "contractor",
}


def default_filters() -> dict:
    """Default filter state: all departments/levels, last 12 months, all types."""
    today = date.today()
    return {
        "departments": [],
        "levels": [],
        "employment_type": None,
        "start_date": (today - timedelta(days=365)).isoformat(),
        "end_date": today.isoformat(),
    }


def normalize_filters(raw: dict) -> dict:
    """Coerce raw widget selections into query-ready filter values.

    'All' selections collapse to None/empty so query builders omit the clause.
    """
    departments = raw.get("departments") or []
    levels = raw.get("levels") or []
    emp_label = raw.get("employment_type", "All")
    return {
        "departments": [d for d in departments if d and d != "All"],
        "levels": [lvl for lvl in levels if lvl and lvl != "All"],
        "employment_type": _EMPLOYMENT_TYPE_MAP.get(emp_label, None),
        "start_date": raw.get("start_date") or default_filters()["start_date"],
        "end_date": raw.get("end_date") or default_filters()["end_date"],
    }


def render_filters(  # pragma: no cover - Streamlit UI glue
    available_departments: list[str], last_refreshed: str | None = None
) -> dict:
    """Render the sidebar and return normalized filter values."""
    import streamlit as st

    defaults = default_filters()
    with st.sidebar:
        st.header("Filters")
        departments = st.multiselect("Department", available_departments, default=[])
        levels = st.multiselect(
            "Level",
            ["IC1", "IC2", "IC3", "IC4", "IC5", "M1", "M2", "M3", "M4"],
            default=[],
        )
        date_range = st.date_input(
            "Date range",
            value=(
                date.fromisoformat(defaults["start_date"]),
                date.fromisoformat(defaults["end_date"]),
            ),
        )
        employment_type = st.radio("Employment type", EMPLOYMENT_TYPE_OPTIONS, index=0)
        if last_refreshed:
            st.caption(f"Last refreshed: {last_refreshed}")

    start, end = (date_range if isinstance(date_range, tuple) else (date_range, date_range))
    return normalize_filters(
        {
            "departments": departments,
            "levels": levels,
            "employment_type": employment_type,
            "start_date": start.isoformat() if start else None,
            "end_date": end.isoformat() if end else None,
        }
    )
