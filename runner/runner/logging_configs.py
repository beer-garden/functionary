from os import getenv

LOG_LEVEL = getenv("LOG_LEVEL", "INFO").upper()
CELERY_LOG_LEVEL = getenv("CELERY_LOG_LEVEL", "WARNING").upper()


formatters = {
    "minimal": {"format": "{asctime} [{levelname:<8}] {message}", "style": "{"},
    "verbose": {
        "format": "{asctime} [{levelname:<8}] {name} {filename}:{funcName}:{lineno} {message}",  # noqa
        "style": "{",
    },
}


# Inside the handlers, update the formatter to be one of the
# defined formatters from above.
handlers = {
    "console": {
        "level": LOG_LEVEL,
        "class": "logging.StreamHandler",
        "formatter": "minimal",
        "stream": "ext://sys.stdout",
    },
    "celery_console": {
        "level": CELERY_LOG_LEVEL,
        "class": "logging.StreamHandler",
        "formatter": "minimal",
        "stream": "ext://sys.stdout",
    },
}


CELERY_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": formatters,
    "handlers": handlers,
    "loggers": {
        "celery": {"handlers": ["celery_console"], "propagate": False},
        "docker": {"propagate": False},
        "kombu": {"propagate": False},
        "urllib3": {"propagate": False},
    },
}

LISTENER_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": formatters,
    "handlers": handlers,
    "loggers": {
        "amqp": {"propagate": False},
        "docker": {"propagate": False},
        "pika": {"propagate": False},
        "runner": {"handlers": ["console"], "propagate": False},
        "urllib3": {"propagate": False},
    },
}
