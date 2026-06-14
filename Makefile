.PHONY: run test lint clean

run:
	streamlit run app.py --server.port 8501

test:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=80

lint:
	ruff check src/ tests/ app.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov
