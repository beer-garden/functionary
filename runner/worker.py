from runner.celery import app
from runner.messaging import wait_for_connection

# TODO: Make various things configurable. Concurrency, etc.
if __name__ == "__main__":
    wait_for_connection()

    worker = app.Worker()
    worker.start()
