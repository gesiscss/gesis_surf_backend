#!/bin/sh

set -e

python manage.py wait_for_db

celery -A app flower --port=5555
