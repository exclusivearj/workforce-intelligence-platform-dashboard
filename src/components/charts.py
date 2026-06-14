"""Shared Plotly chart helpers with a consistent palette and clean labels."""

from __future__ import annotations

PALETTE = ["#FF5A5F", "#00A699", "#FC642D", "#484848", "#767676", "#B4A76C"]
_TEMPLATE = "plotly_white"


def _px():
    import plotly.express as px

    return px


def headcount_line_chart(df, color_by: str = "department"):
    px = _px()
    fig = px.line(
        df, x="date", y="headcount", color=color_by,
        title="Headcount Over Time", template=_TEMPLATE,
        color_discrete_sequence=PALETTE,
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Headcount")
    return fig


def headcount_bar_chart(df):
    px = _px()
    fig = px.bar(
        df, x="headcount", y="department", orientation="h",
        title="Current Headcount by Department", template=_TEMPLATE,
        text="pct_of_total", color_discrete_sequence=PALETTE,
    )
    fig.update_layout(xaxis_title="Headcount", yaxis_title="Department")
    return fig


def attrition_trend_chart(df):
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["year_month"], y=df["attrition_rate_pct"],
        mode="lines+markers", name="Monthly rate", line={"color": PALETTE[0]},
    ))
    fig.add_trace(go.Scatter(
        x=df["year_month"], y=df["rolling_12m_attrition_rate_pct"],
        mode="lines", name="Rolling 12m", line={"color": PALETTE[1]},
    ))
    fig.update_layout(
        title="Attrition Rate Trend", template=_TEMPLATE,
        xaxis_title="Month", yaxis_title="Attrition rate (%)",
    )
    return fig


def attrition_heatmap(df):
    px = _px()
    fig = px.density_heatmap(
        df, x="department", y="total_terminations",
        title="Attrition Intensity by Department", template=_TEMPLATE,
    )
    return fig


def funnel_chart(df):
    import plotly.graph_objects as go

    fig = go.Figure(go.Funnel(y=df["stage"], x=df["count"], marker={"color": PALETTE}))
    fig.update_layout(title="Recruiting Funnel", template=_TEMPLATE)
    return fig


def time_to_hire_chart(df):
    px = _px()
    fig = px.bar(
        df, x="application_to_hire_days_avg", y="job_title", orientation="h",
        title="Average Time to Hire by Role", template=_TEMPLATE,
        color_discrete_sequence=PALETTE,
    )
    fig.update_layout(xaxis_title="Days", yaxis_title="Job title")
    return fig
