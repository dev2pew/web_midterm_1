#!/usr/bin/env bash

# EXIT IMMEDIATELY IF A COMMAND EXITS WITH A NON-ZERO STATUS.
# TREAT UNSET VARIABLES AS AN ERROR WHEN SUBSTITUTING.
# PIPESTATUS IS THE EXIT STATUS OF THE LAST COMMAND IN A PIPELINE.
# THE 'O' PIPEFAIL IS IMPORTANT FOR CATCHING ERRORS IN PIPELINES.

set -euo pipefail

# ENSURE THE SCRIPT IS RUN FROM THE PROJECT ROOT
# CHECKS FOR THE PRESENCE OF 'MANAGE.PY' TO CONFIRM THE LOCATION.

if [ ! -f "manage.py" ]; then
  echo "error... this script must be run from the project root directory."
  exit 1
fi

# LOAD ENVIRONMENT VARIABLES FROM .ENV FILE
# SOURCES ENVIRONMENT VARIABLES SAFELY FROM A .ENV FILE.

if [ -f ".env" ]; then
  # THE 'SET -A' COMMAND EXPORTS ALL VARIABLES CREATED OR MODIFIED.
  # THE 'SET +A' COMMAND DISABLES THIS BEHAVIOR.
  set -a
  source .env
  set +a
else
  echo "error... '.env' file not found."
  exit 1
fi

# DEFINE THE CONTAINER NAME
# HARDCODED FOR THIS PROJECT'S DOCKER-COMPOSE.YML.

POSTGRES_CONTAINER_NAME="web_fileforum_postgres"

# CHECK FOR REQUIRED POSTGRES VARIABLES
# ENSURES THAT NECESSARY DATABASE CREDENTIALS ARE SET.

if [ -z "${POSTGRES_DB-}" ] || [ -z "${POSTGRES_USER-}" ] || [ -z "${POSTGRES_PASSWORD-}" ]; then
    echo "error... one or more required 'POSTGRES_*' environment variables are not set in '.env'."
    exit 1
fi

# CHECK IF THE DOCKER CONTAINER IS RUNNING
# VERIFIES THAT THE TARGET POSTGRESQL CONTAINER IS ACTIVE.

if ! docker ps --filter "name=^/${POSTGRES_CONTAINER_NAME}$" --filter "status=running" --format "{{.Names}}" | grep -q "^${POSTGRES_CONTAINER_NAME}$"; then
    echo "error... the PostgreSQL container '${POSTGRES_CONTAINER_NAME}' is not running."
    echo "please start it with... 'docker compose up -d postgres'"
    exit 1
fi

# USER CONFIRMATION
# A SAFETY CHECK TO PREVENT ACCIDENTAL DATABASE DELETION.

echo "this script will permanently DROP and RECREATE the database inside the Docker container."
echo "container... ${POSTGRES_CONTAINER_NAME}"
echo "user...      ${POSTGRES_USER}"
echo "database...  ${POSTGRES_DB}"

echo ""

read -p "to confirm, please type the database name ('${POSTGRES_DB}') >> " CONFIRMATION
if [ "${CONFIRMATION}" != "${POSTGRES_DB}" ]; then
  echo "confirmation does not match."
  exit 1
fi

# DATABASE OPERATIONS
# DROPS AND RECREATES THE DATABASE INSIDE THE RUNNING CONTAINER.

echo "dropping database '${POSTGRES_DB}' inside container..."
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${POSTGRES_CONTAINER_NAME}" \
  dropdb --if-exists -U "${POSTGRES_USER}" "${POSTGRES_DB}"

echo "creating database '${POSTGRES_DB}' inside container..."
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${POSTGRES_CONTAINER_NAME}" \
  createdb -U "${POSTGRES_USER}" "${POSTGRES_DB}"

# FILE SYSTEM CLEANUP
# REMOVES GENERATED FILES AND CACHES TO ENSURE A CLEAN STATE.

echo "deleting user-generated media and caches..."

# THIS COMMAND IS SAFER AS IT WON'T DELETE THE MEDIA DIRECTORY ITSELF.

find media/ -mindepth 1 -delete

echo "deleting python caches and build artifacts..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
rm -rf .pytest_cache .mypy_cache .ruff_cache .cache .coverage htmlcov

echo "deleting existing migration files..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# DJANGO OPERATIONS
# RECREATES THE DATABASE SCHEMA FROM SCRATCH.

echo "re-creating and applying migrations..."
poetry run python manage.py makemigrations
poetry run python manage.py migrate

# OPTIONAL SUPERUSER CREATION
# PROMPTS THE USER TO CREATE AN ADMIN ACCOUNT.

echo ""

read -p "would you like to create a superuser now >> " CREATE_SUPERUSER
if [[ "${CREATE_SUPERUSER}" =~ ^[Yy]$ ]]; then
    poetry run python manage.py createsuperuser
fi

echo "all done."
