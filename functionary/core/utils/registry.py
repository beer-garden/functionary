"""Helpers for interacting the Docker registry"""
import os

from .constance import get_config


def get_registry_config():
    return get_config(
        [
            "REGISTRY_HOST",
            "REGISTRY_PORT",
            "REGISTRY_NAMESPACE",
            "REGISTRY_USER",
            "REGISTRY_PASSWORD",
        ]
    )


def get_registry(config=None, with_namespace=True):
    """Builds the registry url for the Docker registry"""
    if not config:
        config = get_registry_config()

    registry = os.getenv("REGISTRY_HOST", config.REGISTRY_HOST)
    if port := config.REGISTRY_PORT:
        registry += f":{port}"
    if with_namespace and config.REGISTRY_NAMESPACE:
        registry += f"/{config.REGISTRY_NAMESPACE}"

    return registry
