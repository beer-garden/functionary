import os
import time

import requests


def output_json(input: dict):
    """Demo JSON rendering by accepting JSON input and mirroring it back out"""
    return input


def output_text(input: str):
    """Demo text rendering by accepting string input and mirroring it back out. CSV
    formatted strings will present the option of rendering as a table"""
    return input


def long_running_process(duration: int = 60):
    """Simulates a long running process"""
    time.sleep(duration)


def variables():
    """Print environment variables that got passed through"""
    vars = []
    for name, value in os.environ.items():
        vars.append(f"{name}: {value}")

    output = "\n".join(vars)

    print(output)
    return [{"name": n, "value": v} for n, v in os.environ.items()]


def num_chars(file: str, other_param: str) -> int:
    print(f"Fetching file from this URL: {file}")
    print(f"Here is the other parameter: {other_param}")
    request = requests.get(file)
    if request.status_code == 200:
        return len(request.text)
    return 0


def parameter_types(
    boolean: bool | None = None,
    date: str | None = None,
    datetime: str | None = None,
    file: str | None = None,
    float: float | None = None,
    integer: int | None = None,
    json: dict | None = None,
    string: str | None = None,
    text: str | None = None,
    option_string: str | None = None,
    option_integer: int | None = None,
):
    return [
        {"parameter": "boolean", "type": type(boolean).__name__, "value": boolean},
        {"parameter": "date", "type": type(date).__name__, "value": date},
        {
            "parameter": "datetime",
            "type": type(datetime).__name__,
            "value": datetime,
        },
        {"parameter": "file", "type": type(file).__name__, "value": file},
        {"parameter": "float", "type": type(float).__name__, "value": float},
        {"parameter": "integer", "type": type(integer).__name__, "value": integer},
        {"parameter": "json", "type": type(json).__name__, "value": json},
        {"parameter": "string", "type": type(string).__name__, "value": string},
        {"parameter": "text", "type": type(text).__name__, "value": text},
        {
            "parameter": "option_string",
            "type": type(option_string).__name__,
            "value": option_string,
        },
        {
            "parameter": "option_integer",
            "type": type(option_integer).__name__,
            "value": option_integer,
        },
    ]


def download_url(url: str):
    response = requests.get(url)

    if response.ok:
        try:
            return response.json()
        except Exception:
            return response.text
    else:
        return f"Failed to download. Got response status {response.status_code}."
