#!/bin/sh

set -e

python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrate
celery -A app worker --loglevel=info &
celery -A app flower --port=5555 &


uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi
