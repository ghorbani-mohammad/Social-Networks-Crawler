SHELL=/bin/bash
PYTHON_VERSION=3.11

.PHONY: format
format: format-python

.PHONY: lint
lint: lint-python

.PHONY: format-python
format-python:
	linters/format-python.sh

.PHONY: lint-python
lint-python:
	@MYPYPATH=social linters/lint-python.sh
