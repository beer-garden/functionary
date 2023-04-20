from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Functionary"

    def ready(self) -> None:
        from core import celery
        from core.utils import celery as celery_utils

        celery_utils.configure_celery_app(celery.app, "core")
