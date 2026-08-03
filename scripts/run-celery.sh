#!/bin/sh

set -e

python manage.py wait_for_db
python manage.py wait_for_es

celery -A app worker --loglevel=info
