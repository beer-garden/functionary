from .base import *  # noqa

CELERY_BROKER_URL = "memory://"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}
SECRET_KEY = "testsecret"
