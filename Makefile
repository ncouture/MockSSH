# Default
.PHONY: all
# Build
.PHONY: build
# Test
.PHONY: test tests unit_tests
# Clean up
.PHONY: clean clean_build clean_tests
# Format code
.PHONY: fix lint

PYTHON ?= python
PIP ?= pip
YAPF ?= yapf

UNITTEST = $(PYTHON) -m unittest


all: build


build:
	@python setup.py sdist bdist_wheel

fix:
	@echo 'Auto-formatting code...'
	-@$(YAPF) --in-place --recursive --verify MockSSH.py tests/ examples/

lint:
	@echo 'Checking code format...'
	@$(YAPF) --diff --recursive MockSSH.py tests/ examples/ || (st=$$?; echo 'Please run "make fix" to correct the formatting errors.'; exit $$st)

release: clean build upload_release

upload_release:
	-@$(PIP) install twine
	@twine upload dist/*

test: tests

tests: unit_tests clean_tests

unit_tests: build
	$(UNITTEST) discover -s tests/

clean: clean_build clean_tests

clean_build:
	@python setup.py clean

clean_tests:
	$(call _clean_tests)

define _clean_tests
	@rm -f tests/*.pyc
endef
