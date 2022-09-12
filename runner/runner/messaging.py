import json
import logging
import os
import ssl
from time import sleep

import pika
from pika.exceptions import AMQPConnectionError, UnroutableError

logger = logging.getLogger(__name__)


def build_connection(ca=None, cert=None, key=None, open_callback=None):
    """Creates a connection to RabbitMQ.

    This will use the RABBITMQ_[USER,PASSWORD,HOST,PORT] environment
    variables to open a connection to RabbitMQ. Optionally pass in
    certificate information and/or a callback function.

    Args:
      ca: The path to the CA file for the SSL context
      cert: The path to the user certifcate
      key: The path to the keyfile for the given certificate
      open_callback: If populated, will return a select connection
        with this as the open callback.

    Returns:
      A pika.SelectConnection if open_callback is populated, otherwise
      a pika.BlockingConnection.
    """
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = os.getenv("RABBITMQ_PORT", 5672)
    credentials = None
    ssl_options = None

    if cert:
        context = ssl.create_default_context(cafile=ca)
        context.load_cert_chain(cert, key)
        ssl_options = pika.SSLOptions(context, "localhost")
    else:
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "user"),
            os.getenv("RABBITMQ_PASSWORD", "password"),
        )

    parameters = pika.ConnectionParameters(
        host=host, port=port, credentials=credentials, ssl_options=ssl_options
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
