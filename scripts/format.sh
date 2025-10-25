#!/usr/bin/env bash

set -euo pipefail

# GO TO THE SCRIPT'S DIRECTORY, THEN TO THE PROJECT ROOT

cd "$(dirname "$0")/.."

# DEFAULT TO 'FORMAT' IF NO ARGUMENT IS GIVEN

ACTION=${1:-format}

echo "running isort..."
if [ "$ACTION" == "check" ]; then
    poetry run isort . --check-only --diff
else
    poetry run isort .
fi

echo "running black..."
if [ "$ACTION" == "check" ]; then
    poetry run black . --check --diff
else
    poetry run black .
fi

echo "formatting script complete."
