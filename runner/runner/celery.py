from celery import Celery

app = Celery(
    "runner",
    broker="redis://redis",
    include=["runner.handlers"],
)


if __name__ == "__main__":
    app.start()
