import os

LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "celery": {
            "level": LOG_LEVEL,
        },
        "pika": {
            "level": "WARNING",
        },
    },
}
