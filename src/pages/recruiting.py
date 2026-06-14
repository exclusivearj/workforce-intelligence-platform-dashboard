"""Streamlit page: Recruiting Funnel."""

from __future__ import annotations

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Data",
    "Legal", "Finance", "Recruiting", "HR",
]


def render() -> None:
    import streamlit as st

    from src.components.charts import funnel_chart, time_to_hire_chart
    from src.components.filters import render_filters
    from src.queries.recruiting_queries import (
        get_funnel_summary,
        get_offer_acceptance_rate,
        get_time_to_hire_by_role,
    )

    st.title("Recruiting Funnel")
    filters = render_filters(DEPARTMENTS)
    dept = filters["departments"][0] if filters["departments"] else None

    with st.spinner("Querying Trino..."):
        funnel = get_funnel_summary(department=dept)
        time_to_hire = get_time_to_hire_by_role(department=dept)
        acceptance = get_offer_acceptance_rate(department=dept)

    open_roles = int(time_to_hire["job_title"].nunique()) if not time_to_hire.empty else 0
    avg_tth = (
        float(time_to_hire["application_to_hire_days_avg"].mean())
        if not time_to_hire.empty else 0.0
    )
    avg_accept = (
        float(acceptance["offer_acceptance_rate_pct"].mean())
        if not acceptance.empty else 0.0
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Open Roles", f"{open_roles}")
    c2.metric("Avg Time to Hire", f"{avg_tth:.0f} days")
    c3.metric("Offer Acceptance Rate", f"{avg_accept:.1f}%")

    st.plotly_chart(funnel_chart(funnel), use_container_width=True)
    st.plotly_chart(time_to_hire_chart(time_to_hire), use_container_width=True)
