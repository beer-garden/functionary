import json

import click
from urllib3 import PoolManager
from urllib3.exceptions import ConnectionError, ConnectTimeoutError, MaxRetryError

from functionary.config import get_pool_config


def login(host, user: str, password: str):
    http = PoolManager(**get_pool_config())

    try:
        login_url = f"{host}/api/v1/api-token-auth"
        login_response = http.request(
            "POST", login_url, fields={"username": user, "password": password}
        )
        # check status code/message on return then exit
        if (login_response.status >= 200) and (login_response.status < 300):
            return json.loads(login_response.data).get("token")
        elif login_response.status == 400:
            raise click.ClickException(
                "Unable to login due to an invalid username or password."
            )
        else:
            raise click.ClickException(
                f"Failed to login: {login_response.status}\n"
                f"Response: {login_response.text}"
            )
    except (ConnectionError, MaxRetryError):
        raise click.ClickException(f"Unable to connect to {login_url}.")
    except ConnectTimeoutError:
        raise click.ClickException("Timeout occurred waiting for login")
