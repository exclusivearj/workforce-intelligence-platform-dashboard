"""Streamlit page: Attrition Analysis."""

from __future__ import annotations

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Data",
    "Legal", "Finance", "Recruiting", "HR",
]


def render() -> None:
    import streamlit as st

    from src.components.charts import attrition_heatmap, attrition_trend_chart
    from src.components.filters import render_filters
    from src.queries.attrition_queries import (
        get_attrition_by_department,
        get_attrition_trend,
        get_top_attrition_departments,
    )

    st.title("Attrition Analysis")
    filters = render_filters(DEPARTMENTS)
    dept = filters["departments"][0] if filters["departments"] else None

    with st.spinner("Querying Trino..."):
        trend = get_attrition_trend(department=dept)

    current_rate = float(trend["attrition_rate_pct"].iloc[-1]) if not trend.empty else 0.0
    rolling = (
        float(trend["rolling_12m_attrition_rate_pct"].iloc[-1]) if not trend.empty else 0.0
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Month Rate", f"{current_rate:.1f}%")
    c2.metric("Rolling 12m Rate", f"{rolling:.1f}%")
    c3.metric("YoY Change", "—")

    st.plotly_chart(attrition_trend_chart(trend), use_container_width=True)

    by_dept = get_attrition_by_department()
    st.plotly_chart(attrition_heatmap(by_dept), use_container_width=True)

    st.subheader("Top departments by attrition")
    st.caption("involuntary_terminations is governance-masked for analyst_reader "
               "(restricted — contact HR).")
    st.dataframe(get_top_attrition_departments(5), use_container_width=True)
