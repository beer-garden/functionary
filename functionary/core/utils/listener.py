import json
import logging

from core.utils.messaging import build_connection
from core.utils.tasking import record_task_result

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

    # TODO: Generalize this to support consuming of more than just tasking results
    new_channel.basic_consume("tasking.results", _handle_delivery)


def _handle_delivery(channel, deliver, properties, body):
    """Called when we receive a message from RabbitMQ"""

    # TODO: Implement handling of specific exceptions
    try:
        msg_type = properties.headers.get("x-msg-type", "__NONE__")
        msg_body = json.loads(body.decode())

        logger.info("Received message %s", msg_type)

        match msg_type:
            case "TASK_RESULT":
                record_task_result.delay(msg_body)
            case _:
                logger.error("Unrecognized message type: %s", msg_type)

        channel.basic_ack(deliver.delivery_tag)
    except Exception as exc:
        logger.error("Error handling received message: %s", exc)
