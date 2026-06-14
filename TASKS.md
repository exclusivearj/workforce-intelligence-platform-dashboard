# TASKS.md — dashboard/

> Read `../TASKS.md` first for platform-wide rules.
> Requires `ingestion/` dbt models and Trino to be running before this module works.

---

## What this project builds

A three-page Streamlit People Analytics application that:
1. Queries Trino for all data (not Postgres directly — mirrors production pattern)
2. Pre-computes and caches results in Postgres to keep the UI snappy
3. Presents headcount trends, attrition analysis, and recruiting funnel to HR stakeholders
4. Deploys to Streamlit Community Cloud as a public, shareable URL

This directly addresses the Airbnb JD requirement:
> "Build data products, including dashboards and reporting tools (e.g., Streamlit visualization apps),
> that surface actionable insights for non-technical stakeholders."

---

## Directory structure

```
dashboard/
├── TASKS.md                     ← this file
├── README.md
├── Makefile
├── pyproject.toml
├── app.py                       ← Streamlit entry point
├── src/
│   ├── __init__.py
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── headcount.py         ← Page 1: headcount trends
│   │   ├── attrition.py         ← Page 2: attrition analysis
│   │   └── recruiting.py        ← Page 3: recruiting funnel
│   ├── queries/
│   │   ├── __init__.py
│   │   ├── headcount_queries.py ← Trino SQL for headcount page
│   │   ├── attrition_queries.py ← Trino SQL for attrition page
│   │   └── recruiting_queries.py← Trino SQL for recruiting page
│   └── components/
│       ├── __init__.py
│       ├── filters.py           ← shared filter sidebar component
│       ├── charts.py            ← shared Plotly chart helpers
│       └── cache.py             ← Postgres cache read/write
├── airflow/
│   └── dags/
│       └── dashboard_refresh_dag.py
├── docker/
│   └── init_dashboard_schema.sql
├── tests/
│   ├── conftest.py
│   ├── test_queries.py          ← assert query SQL is valid + returns expected columns
│   ├── test_filters.py          ← assert filter component logic
│   └── test_cache.py            ← assert cache read/write
└── .github/
    └── workflows/
        └── dashboard-ci.yml
```

---

## Implementation tasks

### Task 4.0 — Dashboard cache schema (`docker/init_dashboard_schema.sql`)

```sql
CREATE TABLE IF NOT EXISTS dashboard.cache (
    cache_key       VARCHAR(255) PRIMARY KEY,
    data_json       JSONB NOT NULL,
    row_count       INTEGER,
    computed_at     TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ
);

CREATE INDEX idx_cache_expires_at ON dashboard.cache(expires_at);
```

Cache keys follow the pattern: `{page}_{filter_hash}_{date}`.
Example: `headcount_dept=Engineering_2024-01-15`.

---

### Task 4.1 — Trino connection (`src/queries/__init__.py`)

```python
import trino

def get_trino_connection() -> trino.dbapi.Connection:
    return trino.dbapi.connect(
        host=os.getenv("TRINO_HOST", "localhost"),
        port=int(os.getenv("TRINO_PORT", "8080")),
        user=os.getenv("TRINO_USER", "trino"),
        catalog="postgresql",
        schema="analytics",
    )

def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Execute SQL on Trino, return DataFrame. Log query time."""
```

---

### Task 4.2 — Headcount queries (`src/queries/headcount_queries.py`)

All queries run against `postgresql.analytics.fct_headcount_daily` via Trino.

```python
def get_headcount_trend(
    department: str | None = None,
    level: str | None = None,
    employment_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    SELECT date, department, level, SUM(headcount) as headcount
    FROM postgresql.analytics.fct_headcount_daily
    WHERE <dynamic filters>
    GROUP BY date, department, level
    ORDER BY date

    Return columns: date, department, level, headcount
    """

def get_headcount_snapshot(as_of_date: str) -> pd.DataFrame:
    """
    Headcount by department for a single date.
    Return columns: department, headcount, pct_of_total
    """

def get_headcount_by_level(department: str | None = None) -> pd.DataFrame:
    """
    Latest headcount grouped by level.
    Return columns: level, headcount, pct_of_total
    """
```

---

### Task 4.3 — Attrition queries (`src/queries/attrition_queries.py`)

```python
def get_attrition_trend(
    department: str | None = None,
    start_year_month: str | None = None,
    end_year_month: str | None = None,
) -> pd.DataFrame:
    """
    Monthly attrition rate from fct_attrition_monthly.
    Return columns: year_month, department, attrition_rate_pct, rolling_12m_attrition_rate_pct
    """

def get_attrition_by_department(year_month: str | None = None) -> pd.DataFrame:
    """
    Attrition heatmap data: department x tenure_band.
    Return columns: department, voluntary_terminations, involuntary_terminations, total_terminations
    """

def get_top_attrition_departments(n: int = 5) -> pd.DataFrame:
    """Top N departments by rolling 12-month attrition rate."""
```

---

### Task 4.4 — Recruiting queries (`src/queries/recruiting_queries.py`)

```python
def get_funnel_summary(
    department: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    Recruiting funnel from rpt_recruiting_funnel.
    Return columns: stage, count, conversion_rate_pct
    Stages in order: applied, phone_screen, interview, offer, hired
    """

def get_time_to_hire_by_role(department: str | None = None) -> pd.DataFrame:
    """
    Average days from application to hire, by job title.
    Return columns: job_title, department, application_to_hire_days_avg, hired_count
    """

def get_offer_acceptance_rate(department: str | None = None) -> pd.DataFrame:
    """Offer acceptance rate by department."""
```

---

### Task 4.5 — Filter sidebar component (`src/components/filters.py`)

```python
def render_filters(available_departments: list[str]) -> dict:
    """
    Render a consistent left sidebar with:
    - Department multiselect (default: All)
    - Level multiselect (default: All)
    - Date range picker (default: last 12 months)
    - Employment type radio (All / Full-time / Part-time / Contractor)
    - "Last refreshed: {timestamp}" footer text
    Return dict of selected filter values.
    """
```

The sidebar appears identically on all three pages. Import `render_filters` in each page module.

---

### Task 4.6 — Chart helpers (`src/components/charts.py`)

```python
def headcount_line_chart(df: pd.DataFrame, color_by: str = "department") -> go.Figure:
    """Plotly line chart: x=date, y=headcount, color=color_by column."""

def headcount_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Plotly horizontal bar: department vs headcount with % labels."""

def attrition_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Dual-line chart: monthly attrition rate + rolling 12m line."""

def attrition_heatmap(df: pd.DataFrame) -> go.Figure:
    """Plotly heatmap: departments (y) vs attrition_rate_pct (color intensity)."""

def funnel_chart(df: pd.DataFrame) -> go.Figure:
    """Plotly funnel chart: stages in order with counts + conversion rates."""

def time_to_hire_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: job_title vs application_to_hire_days_avg."""
```

All charts use a consistent color palette. Pass `template="plotly_white"` for clean appearance.
Charts must have accessible titles and axis labels (not just variable names).

---

### Task 4.7 — Cache layer (`src/components/cache.py`)

```python
def get_cached(conn, cache_key: str) -> pd.DataFrame | None:
    """
    Look up cache_key in dashboard.cache.
    Return None if not found or expired.
    Deserialise JSON to DataFrame.
    """

def set_cached(conn, cache_key: str, df: pd.DataFrame, ttl_hours: int = 24) -> None:
    """
    Serialise DataFrame to JSON, upsert into dashboard.cache.
    Set expires_at = NOW() + ttl_hours.
    """

def build_cache_key(page: str, filters: dict) -> str:
    """
    Build a deterministic cache key from page name + filter values.
    Example: 'headcount_dept=Engineering|level=IC3_2024-01-15'
    """
```

---

### Task 4.8 — Page implementations

**`src/pages/headcount.py`**:
```python
def render() -> None:
    """
    Streamlit page: Headcount Trends

    Layout:
    - Top row: 3 metric cards (Total Headcount, MoM Change, YoY Change)
    - Left: line chart (headcount over time, colored by department)
    - Right: bar chart (current headcount by department)
    - Bottom: level distribution (bar chart, filterable by department)

    All data from Trino via headcount_queries.py.
    Try cache first; query Trino on cache miss.
    Show spinner during Trino queries.
    Show "Data as of {date}" below each chart.
    Export button: download current view as CSV.
    """
```

**`src/pages/attrition.py`**:
```python
def render() -> None:
    """
    Streamlit page: Attrition Analysis

    Layout:
    - Top row: 3 metric cards (Current Month Rate, Rolling 12m Rate, YoY Change)
    - Trend chart: monthly attrition rate + rolling 12m (dual line)
    - Heatmap: department vs attrition intensity
    - Table: top 5 departments by attrition with trend indicator

    Note: involuntary_terminations uses governance-masked view — show as masked
    if analyst_reader role is active. Add "(restricted — contact HR)" tooltip.
    """
```

**`src/pages/recruiting.py`**:
```python
def render() -> None:
    """
    Streamlit page: Recruiting Funnel

    Layout:
    - Top row: 3 metric cards (Open Roles, Avg Time to Hire, Offer Acceptance Rate)
    - Funnel chart: stages with counts + conversion rates
    - Time to hire: horizontal bar by job title
    - Monthly trend: applications over time (line chart)
    """
```

---

### Task 4.9 — Streamlit app entry point (`app.py`)

```python
import streamlit as st
from src.pages import headcount, attrition, recruiting

st.set_page_config(
    page_title="People Analytics | Workforce Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

page = st.sidebar.selectbox(
    "View",
    ["Headcount", "Attrition", "Recruiting Funnel"],
)

if page == "Headcount":
    headcount.render()
elif page == "Attrition":
    attrition.render()
elif page == "Recruiting Funnel":
    recruiting.render()

st.sidebar.markdown("---")
st.sidebar.caption("workforce-intelligence-platform · [GitHub](https://github.com/yourusername/workforce-intelligence-platform)")
```

---

### Task 4.10 — Airflow DAG (`airflow/dags/dashboard_refresh_dag.py`)

```python
@dag(
    dag_id="dashboard_refresh",
    schedule="0 7 * * *",    # daily 7am — runs after hr_ingestion (6am)
    tags=["dashboard", "people-analytics"],
)
def dashboard_refresh_dag():
    @task
    def refresh_dashboard_cache() -> dict:
        """
        Pre-compute all Trino queries for default filter state.
        Write results to dashboard.cache via cache.set_cached().
        Return stats: keys_refreshed, total_rows_cached.
        """

    @task
    def notify_dashboard_updated(stats: dict) -> None:
        """Send Slack notification with cache refresh stats."""

    stats = refresh_dashboard_cache()
    notify_dashboard_updated(stats)
```

---

### Task 4.11 — Streamlit Cloud deployment

Add a `requirements.txt` (in addition to `pyproject.toml`) because Streamlit Cloud reads
`requirements.txt` directly:

```
streamlit>=1.35
trino>=0.328
pandas>=2.2
plotly>=5.20
psycopg2-binary>=2.9
python-dotenv>=1.0
```

Add a `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF5A5F"      # Airbnb coral — subtle nod to the target company
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F7F7F7"
textColor = "#484848"
font = "sans serif"
```

**Deployment instructions** (include in README):
1. Fork this repo to your GitHub account
2. Go to https://share.streamlit.io and connect your GitHub account
3. Select `dashboard/app.py` as the entry point
4. Add environment variables: `TRINO_HOST`, `TRINO_PORT`, `TRINO_USER`
5. For public demo: point Trino at a cloud Trino instance or use pre-computed static data
6. Copy the public URL and add it to `dashboard/README.md` and the LinkedIn article

---

### Task 4.12 — Tests

**`tests/test_queries.py`**:
- Mock Trino connection with `pytest-mock`
- Assert `get_headcount_trend()` returns a DataFrame with columns: `date`, `department`, `headcount`
- Assert `get_funnel_summary()` returns rows with stages in correct order
- Assert SQL does not contain raw table names — always uses Trino catalog prefix `postgresql.analytics.*`

**`tests/test_cache.py`**:
- Upsert a DataFrame into cache via `set_cached()`
- Retrieve via `get_cached()` and assert DataFrames are equal
- Assert expired cache returns `None`
- Assert `build_cache_key` is deterministic (same inputs → same key)

---

### Task 4.13 — README.md

Include:
1. Purpose statement
2. Screenshot placeholder (`<!-- screenshot -->`) — fill in after deployment
3. Live URL: `[Open dashboard →](https://YOUR-STREAMLIT-URL)` (fill in after deploy)
4. Tech stack table
5. Step-by-step setup for local dev
6. Streamlit Cloud deployment instructions (summary — full detail in TASKS.md)
7. Design decisions:
   - Why Trino (not Postgres direct) — OLAP access pattern, mirrors production
   - Why Postgres cache — avoid Trino cold-query latency on every page load
   - Why export button — non-technical stakeholders need to take data to meetings

---

## Acceptance criteria

- [ ] All three pages render without errors on local Streamlit (`make run`)
- [ ] Filter sidebar works on all three pages
- [ ] Metric cards show correct values (validate against Trino query directly)
- [ ] Cache layer used on all Trino queries (verify via `dashboard.cache` rows)
- [ ] `make test` passes
- [ ] App deployed to Streamlit Community Cloud with public URL
- [ ] Public URL documented in `README.md`
- [ ] Airflow DAG `dashboard_refresh` completes daily without errors
