"""Celery application factory.

Task modules live in ``apps.<app>.tasks`` and are auto-discovered. When
``CELERY_TASK_ALWAYS_EAGER`` is enabled (see settings) tasks execute inline in
the calling process, which lets the whole app run without a broker in
development. The task code itself is identical in both modes.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("job_outreach_assistant")

# All Celery settings live in Django settings behind the CELERY_ namespace.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> str:  # pragma: no cover - diagnostic helper
    return f"Request: {self.request!r}"
