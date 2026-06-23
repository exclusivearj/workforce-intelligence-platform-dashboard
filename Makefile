.PHONY: help install run test lint clean

help:
	@echo ""
	@echo "dashboard — People Analytics Streamlit app"
	@echo "────────────────────────────────────────────────────────────────"
	@echo "  make install   Install the package + dev tooling (pip install -e .[dev])"
	@echo "  make run       Launch the Streamlit app on http://localhost:8501"
	@echo "  make test      Run the test suite with coverage (>=80%)"
	@echo "  make lint      ruff check src/ tests/ app.py"
	@echo "  make clean     Remove caches + coverage artifacts"
	@echo ""
	@echo "Prerequisites for 'make run': the shared infra (Postgres + Trino) must be up"
	@echo "and the ingestion module set up first (creates analytics.* tables). From the"
	@echo "repo root: make infra-up && make ingestion-setup && make ingestion-dbt."
	@echo "Connection defaults (localhost:8080 / localhost:5432) match docker-compose, so"
	@echo "no env vars are needed locally; export TRINO_*/POSTGRES_* only to override."
	@echo ""

install:
	pip install -e ".[dev]"

run:
	streamlit run app.py --server.port 8501

test:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=80

lint:
	ruff check src/ tests/ app.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov .pytest_cache .ruff_cache
