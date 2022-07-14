import json
import logging

from celery import chain

from .handlers import pull_image, publish_result, run_task
from .message_queue import build_connection

logger = logging.getLogger(__name__)


def start_listening():
    connection = build_connection(open_callback=_on_connected)

    try:
        connection.ioloop.start()
    except KeyboardInterrupt:
        connection.close()

        # Loop until we're fully closed, will stop on its own
        connection.ioloop.start()


def _on_connected(connection):
    """Called when we are fully connected to RabbitMQ"""
    logger.debug("connected...")
    connection.channel(on_open_callback=_on_channel_open)


def _on_channel_open(new_channel):
    """Called when our channel has opened"""
    logger.debug("channel opened...")
    global channel
    channel = new_channel
    channel.queue_declare(
        queue="package_runner",
        durable=True,
        exclusive=False,
        auto_delete=False,
        callback=_on_queue_declared,
    )


def _on_queue_declared(frame):
    """Called when RabbitMQ has told us our Queue has been declared"""
    logger.debug("queue declared...")
    channel.basic_consume("package_runner", _handle_delivery)


def _handle_delivery(channel, deliver, properties, body):
    """Called when we receive a message from RabbitMQ"""
    logger.debug("received message!...")

    try:
        msg_type = properties.headers.get("x-msg-type", "__NONE__")
        body_dict = json.loads(body.decode())

        match msg_type:
            case "PULL_IMAGE":
                pull_image.delay(**body_dict)
            case "TASK_PACKAGE":
                run_task_s = run_task.s()
                publish_task_s = publish_result.s("task_status")

                chain(pull_image.s(body_dict), run_task_s, publish_task_s).delay()
            case _:
                logger.error("Unable to determine message type: %s", msg_type)

        channel.basic_ack(deliver.delivery_tag)
    except Exception:
        logger.error("Error handling received message")
