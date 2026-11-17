# Sentinel-Lite tasks. Linux/macOS, or Windows with GNU make and Git Bash's sh on PATH.
ifeq ($(OS),Windows_NT)
PYTHON_BOOT ?= py -3
BIN := .venv/Scripts
else
PYTHON_BOOT ?= python3
BIN := .venv/bin
endif
PY := $(BIN)/python

# Local secrets: make setup writes .env (gitignored); make run/test read it from there.
-include .env
export SENTINEL_API_KEY

# Every cache stays inside the project folder.
export PIP_CACHE_DIR := $(CURDIR)/.cache/pip
export PRE_COMMIT_HOME := $(CURDIR)/.cache/pre-commit
export RUFF_CACHE_DIR := $(CURDIR)/.cache/ruff
export PYTHONDONTWRITEBYTECODE := 1

# Scanner exceptions exist only for seeded bugs that are still open (scripts/open_bugs.py).
BANDIT_SKIPS = $(shell $(PY) scripts/open_bugs.py bandit)
AUDIT_IGNORES = $(shell $(PY) scripts/open_bugs.py pip-audit)

.PHONY: setup run test test-seeded lint register register-check scan audit build check report

setup:
	$(PYTHON_BOOT) -c "import sys; sys.exit('Python 3.11+ required' if sys.version_info < (3, 11) else 0)"
	$(PYTHON_BOOT) -m venv .venv
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet -r requirements.txt -r requirements-dev.txt
	$(PY) scripts/init_env.py
ifndef CI
	git config core.hooksPath .githooks
	$(PY) -m pre_commit install-hooks
endif

run:
	$(PY) -m app

test:
	$(PY) -m pytest -q

# Seeded-bug regression tests as plain tests: each one fails while its bug is open.
test-seeded:
	$(PY) -m pytest -q --runxfail -m seeded

lint:
	$(PY) -m ruff check .

register:
	$(PY) scripts/build_register.py

register-check:
	$(PY) scripts/build_register.py --check

scan:
	$(PY) -m bandit -q -r app $(if $(BANDIT_SKIPS),-s $(BANDIT_SKIPS))

audit:
	$(PY) -m pip_audit --progress-spinner off -r requirements.txt $(AUDIT_IGNORES)

# Build/import check: every module compiles and the app factory starts and serves /health.
build:
	$(PY) -m compileall -q app scripts
	$(PY) -c "from app import create_app; assert create_app().test_client().get('/health').status_code == 200; print('build: app imports and serves /health')"

check: lint register-check test scan audit build

report:
	$(PY) -m app.reports
