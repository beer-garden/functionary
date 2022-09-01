import os

from celery import Celery

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

app = Celery(
    "runner",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    include=["runner.handlers"],
)


if __name__ == "__main__":
    app.start()
