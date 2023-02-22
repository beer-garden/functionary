import os
import time
from datetime import date, datetime

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


def num_chars(file: str) -> int:
    print(f"Fetching file from this URL: {file}")
    request = requests.get(file)
    if request.status_code == 200:
        return len(request.text)
    return 0


def parameter_types(
    boolean_: bool | None = None,
    date_: date | None = None,
    datetime_: datetime | None = None,
    file_: str | None = None,
    float_: float | None = None,
    integer_: int | None = None,
    json_: dict | None = None,
    string_: str | None = None,
    text_: str | None = None,
):
    return [
        {"parameter": "boolean_", "type": type(boolean_).__name__, "value": boolean_},
        {"parameter": "date_", "type": type(date_).__name__, "value": date_},
        {
            "parameter": "datetime_",
            "type": type(datetime_).__name__,
            "value": datetime_,
        },
        {"parameter": "file_", "type": type(file_).__name__, "value": file_},
        {"parameter": "float_", "type": type(float_).__name__, "value": float_},
        {"parameter": "integer_", "type": type(integer_).__name__, "value": integer_},
        {"parameter": "json_", "type": type(json_).__name__, "value": json_},
        {"parameter": "string_", "type": type(string_).__name__, "value": string_},
        {"parameter": "text_", "type": type(text_).__name__, "value": text_},
    ]
