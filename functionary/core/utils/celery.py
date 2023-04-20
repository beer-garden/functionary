import ssl

from celery import Celery

from .rabbitmq import get_broker, get_rabbitmq_config


def configure_celery_app(app: Celery, name: str) -> Celery:
    """Retrieve a properly configured Celery app based on the django settings

    Args:
        name: Celery app name

    Returns:
        Celery app object
    """
    rabbit_config = get_rabbitmq_config()
    conf = {"CELERY_BROKER_URL": get_broker(rabbit_config)}
    app.config_from_object(conf, namespace="CELERY")
    app.conf.task_default_queue = name

    if rabbit_config.RABBITMQ_TLS:
        app.conf.broker_use_ssl = {
            "certfile": rabbit_config.RABBITMQ_CERT,
            "keyfile": rabbit_config.RABBITMQ_KEY,
            "ca_certs": rabbit_config.RABBITMQ_CACERT,
            "cert_reqs": ssl.CERT_REQUIRED,
        }

    return app
