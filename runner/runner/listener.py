import json
import logging

from celery import chain

from .handlers import publish_result, pull_image, run_task
from .messaging import build_connection

logger = logging.getLogger(__name__)


def start_listening():
    logger.info("Starting listener")
    connection = build_connection(open_callback=_on_connection_open)

    try:
        connection.ioloop.start()
    except KeyboardInterrupt:
        connection.close()

        # Loop until we're fully closed, will stop on its own
        connection.ioloop.start()


def _on_connection_open(connection):
    """Called when we are fully connected to RabbitMQ"""
    logger.info("Connected")
    connection.channel(on_open_callback=_on_channel_open)


def _on_channel_open(new_channel):
    """Called when our channel has opened"""
    logger.debug("Channel opened")

    # TODO: The queue to listen on here should come from config generated during
    #       runner registration
    new_channel.basic_consume("public", _handle_delivery)


def _handle_delivery(channel, deliver, properties, body):
    """Called when we receive a message from RabbitMQ"""

    # TODO: Implement handling of specific exceptions
    try:
        msg_type = properties.headers.get("x-msg-type", "__NONE__")
        msg_body = json.loads(body.decode())

        logger.info("Received message %s", msg_type)

        match msg_type:
            case "PULL_IMAGE":
                pull_image.delay(**msg_body)
            case "TASK_PACKAGE":
                pull_image_s = pull_image.s(msg_body)
                run_task_s = run_task.s(task=msg_body)
                publish_task_s = publish_result.s()

                chain(pull_image_s, run_task_s, publish_task_s).delay()
            case _:
                logger.error("Unrecognized message type: %s", msg_type)

        channel.basic_ack(deliver.delivery_tag)
    except Exception as exc:
        logger.error("Error handling received message: %s", exc)
