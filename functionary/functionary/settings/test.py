from .base import *  # noqa

CELERY_BROKER_URL = "memory://"
CONSTANCE_BACKEND = "constance.backends.memory.MemoryBackend"
DATABASES = {"default": DATABASE_CONFIGS["sqlite"]}
SECRET_KEY = "testsecret"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
