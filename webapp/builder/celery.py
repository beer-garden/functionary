from celery import Celery

app = Celery("builder")
app.config_from_object("django.conf:settings", namespace="CELERY")
