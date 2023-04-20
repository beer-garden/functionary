from logging import getLevelName
from multiprocessing import Process
from os import getenv

from celery.apps.worker import Worker as CeleryWorker
from setproctitle import setproctitle

from runner.celery import WORKER_CONCURRENCY, WORKER_HOSTNAME, app
from runner.listener import start_listening
from runner.messaging import wait_for_connection


class Worker(Process):
    """Celery Worker process

    This class spawns a Celery App that runs a Worker, which will
    ingest and execute tasks from a Redis instance.

    Attributes:
        name: Identification name given to the process
        app: Celery App used to create Celery Workers
    """

    def __init__(self, name: str = "functionary: runner worker") -> None:
        super().__init__(name=name)
        self.app = app
        self.loglevel = getLevelName(getenv("CELERY_LOG_LEVEL", "WARNING").upper())

    def run(self) -> None:
        """Runs the Worker process

        Invoked when the Worker class is started. Worker will create a
        Celery App Worker, connect to the Redis message broker, and listen
        for task events. When a task is discovered, Worker will execute the
        task and publish the results to the message broker.

        Args:
            None

        Returns:
            None

        Raises:
            pika.exceptions.UnroutableError: if unable to publish the message
            pika.exceptions.AMQPConnectionError: failed to connect to message broker
            Exception: catch all exception

        """
        # This will get overridden by celery, but set it anyway so that the process
        # name is correct if anything happens prior to celery forking the workers
        setproctitle(self.name)

        wait_for_connection()
        worker = CeleryWorker(app=self.app, hostname=WORKER_HOSTNAME)
        worker.setup_defaults(concurrency=WORKER_CONCURRENCY, loglevel=self.loglevel)
        worker.start()


class Listener(Process):
    """Listener and Tasking Process

    Reads and Sends event messages from a RabbitMQ message broker.

    Attributes:
        name: Identification name given to the process

    """

    def __init__(self, name: str = "functionary: runner listener") -> None:
        super().__init__(name=name)

    def run(self) -> None:
        """Runs the Listener process

        Invoked when the Listener class is started. Listener will
        connect to the RabbitMQ message broker and listen for event messages.

        Args:
            None

        Returns:
            None

        Raises:
            pika.exceptions.UnroutableError: if unable to publish the message
            pika.exceptions.AMQPConnectionError: failed to connect to message broker
            Exception: catch all exception

        """
        setproctitle(self.name)
        wait_for_connection()
        start_listening()
