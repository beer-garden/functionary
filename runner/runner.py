import logging
import os

from runner import Listener, Worker

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logging.getLogger("pika").propagate = False


def setup_broker_dir() -> None:
    broker_workdir = os.getenv("BROKER_WORKDIR", "/tmp")
    broker_workdir_path = os.path.join(broker_workdir, "broker")
    try:
        if not os.path.exists(broker_workdir_path):
            os.makedirs(os.path.join(broker_workdir_path))
    except PermissionError:
        raise PermissionError(
            f"You do not have permission to create {broker_workdir_path}"
        )


def spawn_listener() -> Listener:
    listener = Listener()
    listener.start()

    return listener


def spawn_worker() -> Worker:
    worker = Worker()
    worker.start()

    return worker


if __name__ == "__main__":
    setup_broker_dir()
    listener = spawn_listener()
    worker = spawn_worker()

    logging.debug("Started worker and listener processes")

    # Explicitly wait on the processes, otherwise when debugging the main process will
    # immediately exit.
    listener.join()
    worker.join()
