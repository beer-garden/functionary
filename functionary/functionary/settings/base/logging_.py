from os import getenv

LOG_LEVEL = getenv("LOG_LEVEL", "INFO").upper()


formatters = {
    "minimal": {"format": "{asctime} [{levelname:<8}] {message}", "style": "{"},
    "verbose": {
        "format": "{asctime} [{levelname:<8}] {name} {filename}:{funcName}:{lineno} {message}",  # noqa
        "style": "{",
    },
}


"""
Inside the handlers, update the formatter to be one of the
defined formatters from above.
"""
handlers = {
    "console": {
        "level": LOG_LEVEL,
        "class": "logging.StreamHandler",
        "formatter": "minimal",
        "stream": "ext://sys.stdout",
    },
}


# Celery Logging Config
CELERY_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": formatters,
    "handlers": handlers,
    "loggers": {
        "celery": {"handlers": ["console"], "propagate": False},
        "docker": {"propagate": False},
        "kombu": {"handlers": ["console"], "propagate": False},
        "urllib3": {"propagate": False},
        "celery.beat": {"propogate": False},
    },
}


# Django Logging Config
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": formatters,
    "handlers": handlers,
    "loggers": {
        "amqp": {"propagate": False},
        "core": {"handlers": ["console"], "propagate": False},
        "django": {"handlers": ["console"], "propagate": False},
        "docker": {"propagate": False},
        "pika": {"propagate": False},
        "urllib3": {"propagate": False},
    },
}
