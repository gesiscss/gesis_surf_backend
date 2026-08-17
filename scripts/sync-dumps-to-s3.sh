#!/bin/sh

set -eu

S3_BUCKET="${S3_BUCKET:-gesis-surf-greek-dumps}"
S3_PREFIX="${S3_PREFIX:-}"
AWS_REGION="${AWS_REGION:-eu-central-1}"
ANALYTICS_DIR="${ANALYTICS_DIR:-data-dumps}"
BACKUPS_DIR="${BACKUPS_DIR:-backups}"

if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

if ! command -v aws >/dev/null 2>&1; then
    echo "aws CLI is not installed or not on PATH." >&2
    exit 1
fi

prefix_path=""
if [ -n "${S3_PREFIX:-}" ]; then
    prefix_path="$(printf "%s" "$S3_PREFIX" | sed 's#/*$##')/"
fi

if [ -d "$ANALYTICS_DIR" ]; then
    aws s3 sync "$ANALYTICS_DIR" "s3://${S3_BUCKET}/${prefix_path}data-dumps/" \
        --region "$AWS_REGION" \
        --sse AES256 \
        --only-show-errors
fi

if [ -d "$BACKUPS_DIR" ]; then
    aws s3 sync "$BACKUPS_DIR" "s3://${S3_BUCKET}/${prefix_path}backups/" \
        --region "$AWS_REGION" \
        --sse AES256 \
        --only-show-errors
fi

echo "Synced dumps to s3://${S3_BUCKET}/${prefix_path}"
