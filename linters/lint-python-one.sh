#!/usr/bin/env bash

set -e

black -t py311 --check "$@"
pylint --rcfile .pylintrc "$@"
flake8 --max-line-length 90 "$@"
mypy --config=./.mypy.ini "$@"
