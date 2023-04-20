"""Celery Worker App

Instantiates a Celery App that will connect to a Redis instance
to retrieve its internal queue of work to perform.

"""
import ssl
from logging.config import dictConfig
from multiprocessing import cpu_count

from celery import Celery
from celery.signals import setup_logging

from . import config
from .logging_configs import CELERY_LOGGING

WORKER_CONCURRENCY = cpu_count()
WORKER_HOSTNAME = "worker"
WORKER_NAME = f"celery@{WORKER_HOSTNAME}"

protocol = "amqps" if config.RABBITMQ_TLS else "amqp"

app = Celery(
    "runner",
    include=["runner.handlers"],
    broker=(
        f"{protocol}://{config.RABBITMQ_USER}:{config.RABBITMQ_PASSWORD}"
        f"@{config.RABBITMQ_HOST}:{config.RABBITMQ_PORT}/{config.RABBITMQ_VHOST}"
    ),
)

if config.RABBITMQ_TLS:
    app.conf.broker_use_ssl = {
        "certfile": config.RABBITMQ_CERT,
        "keyfile": config.RABBITMQ_KEY,
        "ca_certs": config.RABBITMQ_CACERT,
        "cert_reqs": ssl.CERT_REQUIRED,
    }


@setup_logging.connect
def config_loggers(*args, **kwargs):
    dictConfig(CELERY_LOGGING)
