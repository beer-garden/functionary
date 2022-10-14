import logging
import os

from runner import Listener, Worker

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logging.getLogger("pika").propagate = False


def spawn_listener():
    listener = Listener()
    listener.start()

    return listener


def spawn_worker():
    worker = Worker()
    worker.start()

    return worker


if __name__ == "__main__":
    listener = spawn_listener()
    worker = spawn_worker()

    logging.debug("Started worker and listener processes")

    # Explicitly wait on the processes, otherwise when debugging the main process will
    # immediately exit.
    listener.join()
    worker.join()
