from json import loads
from logging import getLogger
from logging.config import dictConfig
from time import sleep

from celery import chain
from celery.app.control import Inspect
from pika.channel import Channel
from pika.spec import Basic, BasicProperties

from .celery import WORKER_CONCURRENCY, WORKER_NAME, app
from .handlers import publish_result, pull_image, run_task
from .logging_configs import LISTENER_LOGGING
from .messaging import build_connection

logger = getLogger(__name__)
dictConfig(LISTENER_LOGGING)

WAIT_FOR_AVAILABLE_WORKER_DELAY = 2
WAIT_FOR_MESSAGE_DELAY = 0.5


def start_listening():
    logger.info("Starting listener")
    connection = build_connection()
    channel = connection.channel()

    inspect = _get_inspect()

    while True:
        method, properties, body = channel.basic_get("public")

        if method is None:
            sleep(WAIT_FOR_MESSAGE_DELAY)
            continue

        _handle_delivery(channel, method, properties, body)
        _wait_for_available_worker(inspect)


def _handle_delivery(
    channel: Channel, method: Basic.GetOk, properties: BasicProperties, body: bytes
):
    """Called when we receive a message from RabbitMQ"""

    # TODO: Implement handling of specific exceptions
    try:
        msg_type = properties.headers.get("x-msg-type", "__NONE__")
        msg_body = loads(body.decode())

        match msg_type:
            case "PULL_IMAGE":
                pull_image.delay(package=msg_body)
            case "TASK_PACKAGE":
                run_task_s = run_task.s(task=msg_body)
                publish_result_s = publish_result.s()

                chain(run_task_s, publish_result_s).delay()
            case _:
                logger.error("Unrecognized message type: %s", msg_type)

        channel.basic_ack(method.delivery_tag)
    except Exception as exc:
        logger.error("Error handling received message: %s", exc)


def _get_inspect() -> Inspect:
    """Return Celery Inspect object after connection to Celery Workers is established"""
    inspect = Inspect(app=app)
    while inspect.ping() is None:
        logger.info("Waiting for connection to Celery workers to be established.")
        sleep(1)

    logger.info("Connection to Celery workers has been established.")
    return inspect


def _get_current_worker_tasks(inspect: Inspect) -> list[dict]:
    """Get the number of tasks that the Celery worker is processing

    Returns a dictionary containing the number of tasks the worker
    is currently processing.
    """
    return inspect.active()[WORKER_NAME]


def _get_worker_concurrency() -> int:
    """Return the concurrency amount for the workers"""
    return WORKER_CONCURRENCY


def _has_available_worker(inspect: Inspect) -> bool:
    """Check if there are any available worker processes"""
    worker_tasks = _get_current_worker_tasks(inspect)
    worker_concurrency = _get_worker_concurrency()

    logger.debug(f"List of worker tasks: {worker_tasks}")
    logger.debug(f"Worker's concurrency amount: {worker_concurrency}")

    return True if len(worker_tasks) < worker_concurrency else False


def _wait_for_available_worker(inspect: Inspect) -> None:
    """Wait for an available worker process before consuming another message"""
    while not _has_available_worker(inspect):
        logger.info(
            "No available worker processes. "
            f"Checking again in {WAIT_FOR_AVAILABLE_WORKER_DELAY} seconds."
        )
        sleep(WAIT_FOR_AVAILABLE_WORKER_DELAY)
