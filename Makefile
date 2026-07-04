VENV ?= .venv
PYTHON := $(VENV)/bin/python

.PHONY: install lint format typecheck test smoke report precommit docker-test

install:
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"
	$(VENV)/bin/pre-commit install

lint:
	$(VENV)/bin/ruff check src tests
	$(VENV)/bin/ruff format --check src tests

format:
	$(VENV)/bin/ruff check --fix src tests
	$(VENV)/bin/ruff format src tests

typecheck:
	$(VENV)/bin/mypy

test:
	$(PYTHON) -m pytest

smoke:
	$(PYTHON) -m pytest -m smoke

report:
	$(PYTHON) -m pytest --html=reports/report.html --self-contained-html

precommit:
	$(VENV)/bin/pre-commit run --all-files

# Hermetic run: restful-booker + suite in containers, report lands in ./reports.
# Pre-creating reports/ keeps it owned by the invoking user, not root.
docker-test:
	mkdir -p reports
	docker compose run --build --rm tests; status=$$?; docker compose down; exit $$status
