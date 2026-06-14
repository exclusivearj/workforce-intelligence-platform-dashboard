"""Streamlit entry point for the People Analytics dashboard."""

from __future__ import annotations

import streamlit as st

from src.pages import attrition, headcount, recruiting

st.set_page_config(
    page_title="People Analytics | Workforce Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "Headcount": headcount.render,
    "Attrition": attrition.render,
    "Recruiting Funnel": recruiting.render,
}

choice = st.sidebar.selectbox("View", list(PAGES.keys()))
PAGES[choice]()

st.sidebar.markdown("---")
st.sidebar.caption(
    "workforce-intelligence-platform · "
    "[GitHub](https://github.com/yourusername/workforce-intelligence-platform)"
)
