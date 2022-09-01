import json
import logging
import ssl
from typing import Tuple

import pika
from django.conf import settings
from pika.exceptions import UnroutableError
from pika.exchange_type import ExchangeType

logger = logging.getLogger(__name__)

PUBLIC_EXCHANGE = "runners.public"
PUBLIC_QUEUE = "public"
TASK_RESULTS_QUEUE = "tasking.results"


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
    connection_params = {
        "host": settings.RABBITMQ_HOST,
        "port": settings.RABBITMQ_PORT,
    }

    if cert:
        context = ssl.create_default_context(cafile=ca)
        context.load_cert_chain(cert, key)
        connection_params["ssl_options"] = pika.SSLOptions(context, "localhost")
    elif settings.RABBITMQ_USER is not None:
        connection_params["credentials"] = pika.PlainCredentials(
            settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
        )

    if open_callback:
        return pika.SelectConnection(
            pika.ConnectionParameters(**connection_params),
            on_open_callback=open_callback,
        )
    else:
        return pika.BlockingConnection(pika.ConnectionParameters(**connection_params))


def get_route(task) -> Tuple[str, str]:
    """Determine the correct exchange and routing key for provided task

    Args:
        task: Task instance to determine routing information for

    Returns:
        A tuple of strings: (exchange, routing_key)
    """
    # TODO: Implement actual routing determination logic. For now, this always returns
    #       the public runner pool exchange and routing key
    return (PUBLIC_EXCHANGE, PUBLIC_QUEUE)


def send_message(exchange, routing_key, msg_type, message):
    """Sends a JSON message to the specified queue.

    Sends the given message to the queue. If msg_type is populated, it
    sets the x-msg-type header to that value.

    Args:
        exchange: The message broker exchange to send the message to
        routing_key: The routing key to use when delivering the message
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
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=publish_props,
            mandatory=True,
        )
    except UnroutableError as ue:
        # TODO revisit this and handle exceptions better. Currently used for retry logic
        logger.error("Failed to send message to %s using %s", exchange, routing_key)
        raise ue
    finally:
        connection.close()


def initialize_messaging():
    """Declares the exchanges and queues necessary for communicating with the runners"""
    connection = build_connection()
    channel = connection.channel()

    logger.debug("Configuring rabbitmq exchange: %s", PUBLIC_EXCHANGE)
    channel.exchange_declare(
        PUBLIC_EXCHANGE,
        exchange_type=ExchangeType.direct,
        durable=True,
        auto_delete=False,
    )
    logger.debug("Configuring rabbitmq queue: %s", PUBLIC_QUEUE)
    channel.queue_declare(PUBLIC_QUEUE, durable=True, auto_delete=False)
    channel.queue_bind(PUBLIC_QUEUE, PUBLIC_EXCHANGE)

    logger.debug("Configuring rabbitmq queue: %s", TASK_RESULTS_QUEUE)
    channel.queue_declare(TASK_RESULTS_QUEUE, durable=True, auto_delete=False)

    channel.close()
    connection.close()
