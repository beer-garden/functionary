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


def refreshAccessToken(login_url: str, tokens):
    message = "Refresh successful!"
    success = False

    try:
        refresh_response = requests.post(
            f"{login_url}refresh/", data={"refresh": tokens["refresh"]}
        )

        # check status code/message on return then exit
        if refresh_response.ok:
            token = json.loads(refresh_response.text)
            tokens["access"] = token["access"]
            success = True
        else:
            message = (
                f"Failed to login: {refresh_response.status_code}\n"
                f"\tResponse: {refresh_response.text}"
            )
    except requests.ConnectionError:
        message = f"Unable to connect to {login_url}"
    except requests.Timeout:
        message = "Timeout occurred waiting for login"

    return success, message, tokens["access"]


def verifyToken(login_url: str, token: str):
    message = "Token verified!"
    success = False

    try:
        verify_response = requests.post(f"{login_url}verify/", data={"token": token})

        # check status code/message on return then exit
        if verify_response.ok:
            success = True
        else:
            message = (
                f"Failed to login: {verify_response.status_code}\n"
                f"\tResponse: {verify_response.text}"
            )
    except requests.ConnectionError:
        message = f"Unable to connect to {login_url}verify"
    except requests.Timeout:
        message = "Timeout occurred waiting for verify"

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
            f"access={tokens['access']}\n"
            f"refresh={tokens['refresh']}\n"
            f"login_url={tokens['login_url']}"
        )


def getTokens():
    tokensFile = Path.home() / ".bg" / "tokens"

    config = {
        **dotenv_values(str(tokensFile)),
    }

    login_url = config["login_url"]
    if not verifyToken(login_url, config["access"])[0]:
        if verifyToken(login_url, config["refresh"])[0]:
            success, _, token = refreshAccessToken(login_url, config)
            if not success:
                raise TokenError("Unable to refresh token")

            config["access"] = token
            saveTokens(config)
        else:
            raise TokenError("Tokens have expired")

    return config["access"], config["refresh"]
