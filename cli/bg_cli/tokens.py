import json
from pathlib import Path

import requests
from dotenv import dotenv_values


class TokenError(Exception):
    pass


def login(login_url: str, user: str, password: str):
    message = "Login successful!"
    success = False

    try:
        login_response = requests.post(
            f"{login_url}", data={"username": user, "password": password}
        )

        # check status code/message on return then exit
        if login_response.ok:
            tokens = json.loads(login_response.text)
            tokens["token"] = tokens["access"]
            tokens["login_url"] = login_url
            saveTokens(tokens)
            success = True
        else:
            message = (
                f"Failed to login: {login_response.status_code}\n"
                f"\tResponse: {login_response.text}"
            )
    except requests.ConnectionError:
        message = f"Unable to connect to {login_url}"
    except requests.Timeout:
        message = "Timeout occurred waiting for login"

    return success, message


def saveTokens(tokens):
    if not tokens or len(tokens) == 0:
        raise ValueError("No tokens to save")

    bgDir = Path.home() / ".bg"
    if not bgDir.exists():
        bgDir.mkdir()

    tokensFile = bgDir / "tokens"
    with tokensFile.open("wt"):
        tokensFile.write_text(
            f"token={tokens['token']}\n"
            f"login_url={tokens['login_url']}"
        )


def getToken():
    tokensFile = Path.home() / ".bg" / "tokens"

    config = {
        **dotenv_values(str(tokensFile)),
    }

    return config["token"]
