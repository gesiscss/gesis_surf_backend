"""
Celery configuration
"""

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

# create a new Celery instance
app = Celery("app")

# load the celery configuration from the Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# discover tasks in all applications in the Django project
app.autodiscover_tasks()
