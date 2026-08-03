#!/bin/sh

set -e

python manage.py wait_for_db
python manage.py wait_for_es
python manage.py collectstatic --noinput

uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi
