SHELL=/bin/bash
PYTHON_VERSION=3.11

.PHONY: format
format: format-python

.PHONY: lint
lint: lint-python

.PHONY: format-python
format-python:
	linter/format-python.sh

.PHONY: lint-python
lint-python:
	@MYPYPATH=social linter/lint-python.sh
