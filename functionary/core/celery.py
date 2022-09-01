from celery import Celery

app = Celery("core", include=["core.utils.tasking"])
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_default_queue = "core"
