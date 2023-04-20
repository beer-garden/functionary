from django.apps import AppConfig


class BuilderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "builder"

    def ready(self) -> None:
        from builder import celery
        from core.utils import celery as celery_utils

        celery_utils.configure_celery_app(celery.app, "builder")
