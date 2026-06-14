"""Streamlit page: Headcount Trends."""

from __future__ import annotations

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Data",
    "Legal", "Finance", "Recruiting", "HR",
]


def render() -> None:
    import streamlit as st

    from src.components.charts import headcount_bar_chart, headcount_line_chart
    from src.components.filters import render_filters
    from src.queries.headcount_queries import (
        get_headcount_by_level,
        get_headcount_snapshot,
        get_headcount_trend,
    )

    st.title("Headcount Trends")
    filters = render_filters(DEPARTMENTS)
    dept = filters["departments"][0] if filters["departments"] else None
    level = filters["levels"][0] if filters["levels"] else None

    with st.spinner("Querying Trino..."):
        trend = get_headcount_trend(
            department=dept,
            level=level,
            employment_type=filters["employment_type"],
            start_date=filters["start_date"],
            end_date=filters["end_date"],
        )

    total = int(trend["headcount"].iloc[-1]) if not trend.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Headcount", f"{total:,}")
    c2.metric("MoM Change", "—")
    c3.metric("YoY Change", "—")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(headcount_line_chart(trend), use_container_width=True)
    with right:
        if not trend.empty:
            snapshot = get_headcount_snapshot(str(trend["date"].max()))
            st.plotly_chart(headcount_bar_chart(snapshot), use_container_width=True)

    st.subheader("Level distribution")
    st.bar_chart(get_headcount_by_level(dept).set_index("level")["headcount"])

    if not trend.empty:
        st.caption(f"Data as of {trend['date'].max()}")
        st.download_button("Export CSV", trend.to_csv(index=False), "headcount.csv")
