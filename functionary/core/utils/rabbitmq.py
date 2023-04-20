"""Helpers for interacting with the rabbitmq management api"""
import os
from typing import Optional

import requests

from .constance import get_config


def get_rabbitmq_config():
    return get_config(
        [
            "RABBITMQ_TLS",
            "RABBITMQ_CERT",
            "RABBITMQ_KEY",
            "RABBITMQ_CACERT",
            "RABBITMQ_HOST",
            "RABBITMQ_PORT",
            "RABBITMQ_MANAGEMENT_PORT",
            "RABBITMQ_USER",
            "RABBITMQ_PASSWORD",
        ]
    )


def get_broker(config) -> str:
    """Builds the RabbitMQ broker address."""
    protocol = "amqps" if config.RABBITMQ_TLS else "amqp"
    host = os.getenv("RABBITMQ_HOST", config.RABBITMQ_HOST)
    port = config.RABBITMQ_PORT
    user = config.RABBITMQ_USER
    password = config.RABBITMQ_PASSWORD
    return f"{protocol}://{user}:{password}@{host}:{port}"


def _get_session(config) -> requests.Session:
    """Builds a Session to use for requests to the management API"""
    username = config.RABBITMQ_USER
    password = config.RABBITMQ_PASSWORD
    cacert = config.RABBITMQ_CACERT
    cert = config.RABBITMQ_CERT
    key = config.RABBITMQ_KEY

    session = requests.Session()

    if username and password:
        session.auth = (username, password)

    if cert and key:
        session.cert = (cert, key)

    if cacert:
        session.verify = cacert

    return session


def create_vhost(name: str, description: Optional[str] = None) -> dict:
    """Create a virtual host

    Args:
      name: The name of the virtual host
      description: Description of the virtual host

    Returns:
      Dict containing the created virtual host's definition from the rabbitmq
      management server.
    """
    config = get_rabbitmq_config()
    protocol = "https" if config.RABBITMQ_TLS else "http"
    base_url = (
        f"{protocol}://{config.RABBITMQ_HOST}:{config.RABBITMQ_MANAGEMENT_PORT}/api"
    )
    url = f"{base_url}/vhosts/{name}"
    data = None

    if description is not None:
        data = {"description": description}

    session = _get_session(config)
    session.put(url, json=data)
    vhost = session.get(url).json()

    return vhost
