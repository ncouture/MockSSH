# Default
.PHONY: all
# Build
.PHONY: build
# Test
.PHONY: test tests unit_tests
# Clean up
.PHONY: clean clean_build clean_tests
# Format code
.PHONY: fix lint typecheck

PYTHON ?= $(shell if [ -d .venv ]; then echo .venv/bin/python; else echo python; fi)
PIP ?= $(shell if [ -d .venv ]; then echo .venv/bin/pip; else echo pip; fi)
RUFF ?= $(shell if [ -x .venv/bin/ruff ]; then echo .venv/bin/ruff; elif [ -d .venv ]; then echo .venv/bin/python -m ruff; else echo ruff; fi)
MYPY ?= $(shell if [ -x .venv/bin/mypy ]; then echo .venv/bin/mypy; elif [ -d .venv ]; then echo .venv/bin/python -m mypy; else echo mypy; fi)

UNITTEST = $(PYTHON) -m unittest


all: unit_tests


build:
	@$(PIP) install build
	@$(PYTHON) -m build

fix:
	@echo 'Auto-formatting code...'
	-@$(RUFF) check --fix .
	-@$(RUFF) format .

lint:
	@echo 'Checking code format and linting...'
	@$(RUFF) check . || (st=$$?; echo 'Please run "make fix" to correct linting errors.'; exit $$st)
	@$(RUFF) format --check . || (st=$$?; echo 'Please run "make fix" to correct formatting errors.'; exit $$st)

typecheck:
	@echo 'Running static type checking...'
	@$(MYPY) MockSSH.py

release: clean build upload_release

upload_release:
	-@$(PIP) install twine
	@twine upload dist/*

test: tests

tests: unit_tests clean_tests

unit_tests: build
	$(PYTHON) -m pytest tests/

clean: clean_build clean_tests clean_keys

clean_build:
	@rm -rf build dist *.egg-info .eggs
	@find . -type d -name __pycache__ -exec rm -rf "{}" +

clean_keys:
	@rm -f id_ecdsa id_ed25519 id_rsa

clean_tests:
	$(call _clean_tests)

define _clean_tests
	@rm -f tests/*.pyc
endef
