SHELL := /bin/bash

.PHONY: install test check clean build publish quickstart venv

venv:
	which uv >/dev/null 2>&1 || (echo "Install uv: astral.sh/uv" && exit 1)
	uv venv .venv --python 3.12
	uv pip install -e ".[test]"
	@echo ""
	@echo "Done! Activate with: source .venv/bin/activate"

install:
	which uv >/dev/null 2>&1 || (echo "Install uv: astral.sh/uv" && exit 1)
	uv pip install -e ".[test]"

test:
	uv run pytest tests/unit/ -v

test-cov:
	uv run pytest tests/unit/ -v --cov=whiz --cov-report=term-missing

check:
	uv run pytest tests/unit/ -v

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

build:
	hatch build

publish:
	hatch publish

quickstart:
	@echo "Whiz v0.1.0 -- Quick Start"
	@echo ""
	@echo "1. Install:  make venv && source .venv/bin/activate"
	@echo "2. Key:      export OPENROUTER_API_KEY=*** ""
	@echo "3. Run:      whiz run 'your task here'"
	@echo ""
	@echo "Or without venv:"
	@echo "   uv run whiz run 'your task here'"
