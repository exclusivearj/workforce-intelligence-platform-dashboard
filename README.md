![workforce-intelligence-platform-dashboard banner](assets/04-dashboard-banner.png)

# workforce-intelligence-platform-dashboard — People Analytics Streamlit app

Part 4 of 4 in the [workforce-intelligence-platform](../README.md).

A three-page Streamlit application surfacing headcount trends, attrition analysis,
and recruiting funnel metrics for non-technical HR stakeholders.

---

## Live demo

[Open dashboard →](https://YOUR-STREAMLIT-URL)
<!-- Replace with Streamlit Community Cloud URL after deployment -->

---

## Architecture

```
  Trino (OLAP layer)
  postgresql.analytics.*
         │
         ├── fct_headcount_daily   ──►  Page 1: Headcount
         ├── fct_attrition_monthly ──►  Page 2: Attrition
         └── rpt_recruiting_funnel ──►  Page 3: Recruiting
                  │
                  ▼
        dashboard.cache (Postgres)
        pre-computed query results
                  │
                  ▼
          Streamlit app (app.py)
          Deployed: Streamlit Community Cloud
                  │
                  ▼
        Airflow DAG: dashboard_refresh (daily 7am)
```

---

## Tech stack

| Concern | Technology |
|---|---|
| Frontend | Streamlit 1.35+ |
| Charts | Plotly |
| Analytical SQL | Trino 438 (via trino Python client) |
| Cache | Postgres 16 (dashboard.cache table) |
| Orchestration | Apache Airflow 2.9 |
| Testing | pytest + pytest-mock |
| Deployment | Streamlit Community Cloud (free) |

---

## Setup (local)

```bash
cd dashboard
pip install -e ".[dev]"
# ensure TRINO_HOST, TRINO_PORT, TRINO_USER are in your .env
make run           # launches Streamlit at http://localhost:8501
```

---

## Streamlit Cloud deployment

1. Fork this repo to your GitHub account
2. Go to https://share.streamlit.io → New app
3. Repository: `yourusername/workforce-intelligence-platform`
4. Branch: `main`
5. Main file path: `dashboard/app.py`
6. Add secrets: `TRINO_HOST`, `TRINO_PORT`, `TRINO_USER`
7. Deploy → copy public URL into this README

---

## Make targets

| Target | Description |
|---|---|
| `make run` | Start Streamlit on :8501 |
| `make test` | Run test suite |
| `make lint` | ruff check |

---

## Design decisions

**Trino not direct Postgres.** Dashboards query Trino, which is the OLAP layer. This keeps
separation between transactional writes (Postgres) and analytical reads (Trino) — the same
pattern used at production scale. It also means query optimisation happens at the Trino layer
and dashboard code never needs to tune Postgres indexes.

**Postgres cache.** Trino queries on cold start can take 2-5 seconds. Pre-computing results
during the daily Airflow cache refresh means the dashboard loads in under 500ms for common
filter combinations. Cache misses fall through to live Trino queries with a spinner.

**Export button on every page.** HR partners, Recruiters, and Legal take data to meetings.
A CSV export that matches exactly what they see on screen eliminates the "send me the raw data"
request and reduces analytical bottlenecks.
