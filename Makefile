.PHONY: install test check clean build publish

install:
	pip install -e ".[test]"

test:
	pytest tests/unit/ -v

test-cov:
	pytest tests/unit/ -v --cov=whiz --cov-report=term-missing

test-e2e:
	pytest tests/ -m e2e -v

check:
	python -m pytest tests/unit/ -v

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	hatch build

publish:
	hatch publish

docs-adr:
	@echo "Architecture Decision Records:"
	@ls -1 docs/adr/

quickstart:
	@echo "Whiz v0.1.0 -- Quick Start"
	@echo ""
	@echo "1. Set your API key: export OPENAI_API_KEY=sk-..."
	@echo "2. Run: whiz run 'your task here'"
	@echo "3. Library: from whiz import Session; Session().run('task')"
