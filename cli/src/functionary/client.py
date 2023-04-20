import json

import click
from urllib3 import PoolManager
from urllib3.exceptions import ConnectionError, ConnectTimeoutError, MaxRetryError

from .config import get_config_value, get_pool_config


def get(endpoint):
    """
    Gets any data associated with an endpoint from the api

    Args:
        endpoint: the name of the endpoint to get data from

    Returns:
        Data from endpoint as Python list/dict
    """
    response_data = _send_request(endpoint, "get")

    if "results" in response_data:
        return response_data["results"]
    else:
        return response_data


def post(endpoint, data=None):
    """
    Post provides data or files to endpoint

    Args:
        endpoint: the name of the endpoint to get data from
        data: Any data to put in the request's data field

    Returns:
        Response from endpoint as Python list/dict

    """
    return _send_request(endpoint, "post", post_data=data)


def _400_error_handling(response):
    """
    Helper function for _send_request that gives more user friendly
    responses from 400 error codes

    Args:
        response: Python response object with 400 error
    Raises:
        ClickException with user friendly message based on response
    """
    message = None
    response_data = json.loads(response.data)
    code = response_data["code"]

    if code == "missing_env_header":
        message = (
            "No environment selected. Please set environment id using 'functionary "
            "environment set'.",
        )
    elif code == "invalid_env_header":
        message = (
            "Invalid environment provided. Please set environment using 'functionary "
            "environment set'.",
        )
    else:
        message = f"{response_data['detail']}"
    raise click.ClickException(message)


def _send_request(endpoint, request_type, post_data=None):
    """
    Helper function for get and post that sends the request and handles any errors
    that arise

    Args:
        endpoint: the name of the endpoint to get data from
        request_type: Either post or get
        post_data: Any data to put in the post request's data field

    Returns:
        Response object generated from the request

    Raises:
        ClickException: Raised if cannot connect to host, permission issue
        exists, user has not set a required field, or other request failure
    """
    http = PoolManager(**get_pool_config())
    host = get_config_value("host", raise_exception=True)
    url = f"{host}/api/v1/{endpoint}"
    headers = {"Accept": "application/json"}
    post_data = post_data or {}

    try:
        if (token := get_config_value("token", raise_exception=False)) is not None:
            headers["Authorization"] = f"Token {token}"

        if (
            environment_id := get_config_value(
                "current_environment_id", raise_exception=False
            )
        ) is not None:
            headers["X-Environment-ID"] = f"{environment_id}"

        if request_type == "post":
            response = http.request("POST", url, headers=headers, fields=post_data)
        else:
            response = http.request("GET", url, headers=headers)

    except (ConnectionError, MaxRetryError):
        raise click.ClickException(f"Could not connect to {host}")
    except ConnectTimeoutError:
        raise click.ClickException(f"Timeout occurred waiting for {host}")

    if (response.status >= 200) and (response.status < 300):
        return json.loads(response.data)
    elif response.status == 400:
        _400_error_handling(response)
    elif response.status == 401:
        raise click.ClickException("Authentication failed. Please login and try again.")
    elif response.status == 403:
        raise click.ClickException("You do not have access to perform this action.")
    else:
        raise click.ClickException("An unknown error occurred. Please try again later")
