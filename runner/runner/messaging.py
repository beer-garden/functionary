import json
import logging
import ssl
from time import sleep

import pika
from pika.exceptions import AMQPConnectionError, UnroutableError

from . import config

logger = logging.getLogger(__name__)


def _get_ssl_options() -> pika.SSLOptions | None:
    """Builds the SSLOptions for the pika connection"""
    ssl_options = None

    if config.RABBITMQ_TLS:
        context = ssl.create_default_context()

        if config.RABBITMQ_CACERT:
            context.load_verify_locations(cafile=config.RABBITMQ_CACERT)

        if config.RABBITMQ_CERT and config.RABBITMQ_KEY:
            context.load_cert_chain(config.RABBITMQ_CERT, config.RABBITMQ_KEY)

        ssl_options = pika.SSLOptions(context, config.RABBITMQ_HOST)

    return ssl_options


def _get_credentials() -> pika.PlainCredentials | None:
    """Builds the credentials for the pika connection"""
    return (
        pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
        if config.RABBITMQ_USER and config.RABBITMQ_PASSWORD
        else None
    )


def build_connection(
    open_callback=None,
) -> pika.SelectConnection | pika.BlockingConnection:
    """Creates a connection to RabbitMQ.

    This will use the RABBITMQ_[USER,PASSWORD,HOST,PORT,CACERT,CERT,KEY] environment
    variables to open a connection to RabbitMQ.

    Args:
      open_callback: If populated, will return a select connection
        with this as the open callback.

    Returns:
      A pika.SelectConnection if open_callback is populated, otherwise
      a pika.BlockingConnection.
    """
    ssl_options = _get_ssl_options()
    credentials = _get_credentials()

    parameters = pika.ConnectionParameters(
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        credentials=credentials,
        ssl_options=ssl_options,
    )

    if open_callback:
        return pika.SelectConnection(parameters, on_open_callback=open_callback)
    else:
        return pika.BlockingConnection(parameters)


def send_message(routing_key, msg_type, message):
    """Sends a JSON message to the specified queue.

    Sends the given message to the queue. If msg_type is populated, it
    sets the x-msg-type header to that value.

    Args:
      queue: The name of the queue to send to
      msg_type: The value of x-msg-type to set in the header, or None
      message: The message to send, must be valid JSON.

    Raises:
      pika.exceptions.UnroutableError: if unable to publish the message
    """

    headers = {"x-msg-type": msg_type} if msg_type else {}
    # TODO Update this to use a persistent connection to the queue
    publish_props = pika.BasicProperties(
        content_type="application/json",
        content_encoding="utf-8",
        headers=headers,
        delivery_mode=1,
    )

    connection = build_connection()
    channel = connection.channel()
    channel.confirm_delivery()

    try:
        channel.basic_publish(
            exchange="",
            routing_key=routing_key,
            body=json.dumps(message),
            properties=publish_props,
            mandatory=True,
        )
    except UnroutableError as ue:
        # TODO revisit this and handle exceptions better. Currently used for retry logic
        logger.error("Failed to send message")
        raise ue
    finally:
        connection.close()


def connection_ready() -> bool:
    """Determine if we are able to connect to the message broker

    Returns:
        bool: True if we can connect, False otherwise
    """
    try:
        build_connection()
    except AMQPConnectionError as exc:
        logger.debug("Failed to connect to message broker: %s", exc)

        return False

    return True


def wait_for_connection():
    """Waits for a successful connection to the message broker"""
    logger.info("Checking message broker connection")

    while not connection_ready():
        logger.info("Unable to connect to message broker. Retry in 5s.")
        sleep(5)

    logger.info("Connected to message broker")
