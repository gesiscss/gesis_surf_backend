#!/bin/sh

set -eu

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.deploy.yaml}"
OUTPUT_DIR="${OUTPUT_DIR:-data-dumps}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_FILE="${OUTPUT_DIR}/gesis_surf_tables_${TIMESTAMP}.dump"

DEFAULT_TABLES="
core_user
core_globalsession
core_window
core_tab
core_tab_domains
core_domain
core_click
core_scroll
"

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

TABLE_ARGS=""
if [ "$#" -gt 0 ]; then
    for table in "$@"; do
        TABLE_ARGS="$TABLE_ARGS --table=$table"
    done
else
    for table in $DEFAULT_TABLES; do
        TABLE_ARGS="$TABLE_ARGS --table=$table"
    done
fi

docker compose -f "$COMPOSE_FILE" exec -T db \
    pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --no-owner \
    --no-privileges \
    $TABLE_ARGS \
    > "$OUTPUT_FILE"

echo "$OUTPUT_FILE"
