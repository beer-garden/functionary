import os
import pathlib

import pytest
import requests
from click.testing import CliRunner

from functionary import package
from functionary.config import save_config_value
from functionary.package import get_tar_path, publish


def response_200(*args, **kwargs):
    response = requests.Response()
    response.status_code = 200
    response._content = b"""{
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "creator": {
            "id": 0
        },
        "package": {"id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "name": "string"},
        "created_at": "2023-03-06T18:24:05.051Z",
        "updated_at": "2023-03-06T18:24:05.051Z",
        "status": "PENDING",
        "environment": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    }"""

    return response


def validate_package_mock(path):
    return None


def check_changes_mock(path):
    return True


@pytest.mark.usefixtures("config")
def test_publish_with_keep(fakefs, monkeypatch):
    """Call publish with --keep : Keep build artifacts rather than cleaning them up"""
    monkeypatch.setattr(package, "validate_package", validate_package_mock)
    monkeypatch.setattr(package, "check_changes", check_changes_mock)
    monkeypatch.setattr(requests, "post", response_200)
    os.environ["HOME"] = "/tmp/test_home"
    fakefs.create_file(pathlib.Path.home() / "tar_this.txt")

    host = "http://test:1234"
    save_config_value("host", host)

    runner = CliRunner()
    runner.invoke(publish, [str(pathlib.Path.home()), "--keep", "-y"])
    assert os.path.isfile(get_tar_path(pathlib.Path.home().name))


@pytest.mark.usefixtures("config")
def test_publish_without_keep(fakefs, monkeypatch):
    """Call publish without --keep : Cleaning up build artifacts after publishing"""
    monkeypatch.setattr(package, "validate_package", validate_package_mock)
    monkeypatch.setattr(package, "check_changes", check_changes_mock)
    monkeypatch.setattr(requests, "post", response_200)
    os.environ["HOME"] = "/tmp/test_home"
    fakefs.create_file(pathlib.Path.home() / "tar_this.txt")

    host = "http://test:1234"
    save_config_value("host", host)

    runner = CliRunner()
    runner.invoke(publish, [str(pathlib.Path.home())])
    assert not os.path.isfile(get_tar_path(pathlib.Path.home().name))
