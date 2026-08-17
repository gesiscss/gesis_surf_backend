#!/bin/sh

set -eu

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.deploy.yaml}"
OUTPUT_DIR="${OUTPUT_DIR:-backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_FILE="${OUTPUT_DIR}/full_db_${TIMESTAMP}.dump"

if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

if [ -z "${DB_USER:-}" ] || [ -z "${DB_NAME:-}" ]; then
    echo "DB_USER and DB_NAME must be set in the environment or .env file." >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

docker compose -f "$COMPOSE_FILE" exec -T db \
    pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --no-owner \
    --no-privileges \
    > "$OUTPUT_FILE"

echo "$OUTPUT_FILE"
