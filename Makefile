.PHONY: help install run test lint clean teardown

# Source the canonical platform .env (../.env — the workforce-intelligence-platform dir,
# NOT the workspace root) into a recipe's shell so DB-touching targets honor real
# credentials. Applied to run/teardown only — NOT to test/lint, which stay hermetic.
# Harmless when the file is absent (CI supplies these as real env vars).
LOAD_ENV := set -a; [ -f ../.env ] && . ../.env; set +a

# psql connection string: prefer DATABASE_URL, else assemble from POSTGRES_* using the
# same defaults as src/utils/db.py and docker-compose.yml. Resolved inside the shell so
# sourced/exported env is honored. ON_ERROR_STOP=1 makes a failed statement fail the target.
DSN  = $${DATABASE_URL:-postgresql://$${POSTGRES_USER:-postgres}:$${POSTGRES_PASSWORD:-changeme}@$${POSTGRES_HOST:-localhost}:$${POSTGRES_PORT:-5432}/$${POSTGRES_DB:-workforce}}
PSQL = psql "$(DSN)" -v ON_ERROR_STOP=1

help:
	@echo ""
	@echo "dashboard — People Analytics Streamlit app"
	@echo "────────────────────────────────────────────────────────────────"
	@echo "  make install   Install the package + dev tooling (pip install -e .[dev])"
	@echo "  make run       Launch the Streamlit app on http://localhost:8501"
	@echo "  make test      Run the test suite with coverage (>=80%)"
	@echo "  make lint      ruff check src/ tests/ app.py"
	@echo "  make clean     Remove caches + coverage artifacts"
	@echo "  make teardown  Stop the app, clear dashboard.cache, then stop the shared stack"
	@echo ""
	@echo "Prerequisites for 'make run': the shared infra (Postgres + Trino) must be up"
	@echo "and the ingestion module set up first (creates analytics.* tables). From the"
	@echo "repo root: make infra-up && make ingestion-setup && make ingestion-dbt."
	@echo "Connection defaults (localhost:8080 / localhost:5432) match docker-compose, so"
	@echo "no env vars are needed locally; export TRINO_*/POSTGRES_* (or set them in ../.env)"
	@echo "only to override."
	@echo ""

install:
	pip install -e ".[dev]"

run:
	@$(LOAD_ENV); streamlit run app.py --server.port 8501

test:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=80

lint:
	ruff check src/ tests/ app.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov .pytest_cache .ruff_cache

# Graceful teardown — the inverse of `make run` against a live stack. Stops any local
# Streamlit server, clears the dashboard's own data (TRUNCATE dashboard.cache — the cache
# table is created once on volume init, so it is truncated, not dropped), clears local
# caches, then shuts down the shared Docker stack (repo-root `infra-down`). The DB step
# runs first, while Postgres is still up, and is skipped if it is already down. Volumes are
# preserved (sibling-module data + Airflow metadata survive) — use repo-root
# `make infra-reset` to also wipe them. Re-runnable; `make infra-up` (after ingestion is
# rebuilt) restores a working dashboard.
teardown:
	@echo "Tearing down dashboard (graceful)..."
	@echo "  - stopping any local Streamlit server (host process on :8501)..."
	-@pkill -f "streamlit run app.py" >/dev/null 2>&1 && echo "    stopped local Streamlit" || echo "    none running"
	@echo "  - clearing the dashboard cache (TRUNCATE dashboard.cache; skipped if Postgres is down)..."
	@$(LOAD_ENV); $(PSQL) -c "TRUNCATE TABLE dashboard.cache" >/dev/null 2>&1 \
		&& echo "    cleared dashboard.cache" \
		|| echo "    (Postgres not reachable or table absent — skipped DB cleanup)"
	@$(MAKE) clean
	@echo "  - shutting down the shared Docker stack (postgres/trino/airflow)..."
	@$(MAKE) -C .. infra-down
	@echo "Dashboard teardown complete. Volumes preserved — run repo-root 'make infra-reset' to also wipe them."
