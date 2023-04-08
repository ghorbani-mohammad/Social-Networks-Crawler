#!/usr/bin/env bash

set -e

find social \
	-type d -name migrations -prune -o \
	-type f -name "*.py" \
	-exec "$@" {} +
