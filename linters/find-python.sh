#!/usr/bin/env bash

set -e

find social -type f \
	-name "*.py" \
	-exec "$@" {} +
