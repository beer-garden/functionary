import os
import pathlib
from unittest.mock import Mock

import urllib3
from click.testing import CliRunner

from functionary import package
from functionary.config import save_config_value
from functionary.package import get_tar_path, publish


def buildstatus_response_200(*args, **kwargs):
    response = Mock()
    response.status = 200
    response.data = b"""{
        "id":"12345",
        "creator":{
            "id":1,
            "username": "admin"
        },
        "package":{
            "id":"3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "name":"test"
        },
        "created_at": "2023-03-06T18:24:05.051Z",
        "updated_at": "2023-03-06T18:24:05.051Z",
        "environment": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    }"""
    return response


def package_response_200(*args, **kwargs):
    response = Mock()
    response.status = 200
    response.data = b"""{
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "creator": {
            "id": 0
        },
        "results": [{
            "id":"3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "name":"Package Name",
            "display_name":"Functionality Demo",
            "summary":"Provides functions that demo / test various available features",
            "status":"ACTIVE",
            "language":"python",
            "image_name":"3764e110-2e14-4ab6-a8be-ee7b5b6345d6/demo:291eb717-1be6-4390",
            "environment":"3fa85f64-5717-4562-b3fc-2c963f66afa6"
        }],
        "created_at": "2023-03-06T18:24:05.051Z",
        "updated_at": "2023-03-06T18:24:05.051Z",
        "status": "PENDING",
        "environment": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    }"""

    return response


def function_response_200(*args, **kwargs):
    response = Mock()
    response.status = 200
    response.data = b"""{
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "test",
        "creator": {
        "id": 0
        },
        "results":[{
            "parameters":[{"name":"input","description":"The text to render",
            "type":"text","default":null,"required":true}],
            "name":"Example Name",
            "display_name":"Example Display",
            "summary":"Example Summary",
            "description":"Example Description.",
            "variables":[],
            "return_type":"string",
            "active":true,
            "package": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "environment": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        }]
    }"""

    return response


def validate_package_mock(path):
    return None


def check_changes_mock(path):
    return True


def list_response_mock(manager, method, url, *args, **kwargs):
    if url.split("/")[-1] == "packages":
        return package_response_200(*args, **kwargs)
    else:
        return function_response_200(*args, **kwargs)


def test_publish_with_keep(fakefs, monkeypatch):
    """Call publish with --keep : Keep build artifacts rather than cleaning them up"""
    monkeypatch.setattr(package, "validate_package", validate_package_mock)
    monkeypatch.setattr(package, "check_changes", check_changes_mock)
    monkeypatch.setattr(urllib3.PoolManager, "request", package_response_200)
    os.environ["HOME"] = "/tmp/test_home"
    fakefs.create_file(pathlib.Path.home() / "tar_this.txt")

    host = "http://test:1234"
    save_config_value("host", host)

    runner = CliRunner()
    runner.invoke(publish, [str(pathlib.Path.home()), "--keep", "-y"])
    assert os.path.isfile(get_tar_path(pathlib.Path.home().name))


def test_publish_without_keep(fakefs, monkeypatch):
    """Call publish without --keep : Cleaning up build artifacts after publishing"""
    monkeypatch.setattr(package, "validate_package", validate_package_mock)
    monkeypatch.setattr(package, "check_changes", check_changes_mock)
    monkeypatch.setattr(urllib3.PoolManager, "request", package_response_200)
    os.environ["HOME"] = "/tmp/test_home"
    fakefs.create_file(pathlib.Path.home() / "tar_this.txt")

    host = "http://test:1234"
    save_config_value("host", host)

    runner = CliRunner()
    runner.invoke(publish, [str(pathlib.Path.home())])
    assert not os.path.isfile(get_tar_path(pathlib.Path.home().name))


def test_list(monkeypatch):
    monkeypatch.setattr(urllib3.PoolManager, "request", list_response_mock)
    host = "http://test:1234"
    save_config_value("host", host)

    runner = CliRunner()
    table = runner.invoke(package.list)
    assert "Example Name" in table.stdout


def test_buildstatus(monkeypatch):
    monkeypatch.setattr(urllib3.PoolManager, "request", buildstatus_response_200)
    host = "http://test:1234"
    save_config_value("host", host)

    runner = CliRunner()
    table = runner.invoke(
        package.buildstatus, "--id 3fa85f64-5717-4562-b3fc-2c963f66afa6"
    )
    assert "test" in table.output


def test_create(mocker, fakefs):
    fakefs.create_dir("/arbitrary/path")
    mocker.patch("shutil.copytree")
    mocker.patch("functionary.package._generate_yaml")

    runner = CliRunner()
    options = "-l python -o /arbitrary path"
    result = runner.invoke(package.create_cmd, options)
    assert "Package creation for path successful" in result.output
