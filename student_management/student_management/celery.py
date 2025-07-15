import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "student_management.settings")

app = Celery("student_management")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
