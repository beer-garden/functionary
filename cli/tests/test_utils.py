from unittest.mock import Mock

import pytest
import urllib3

from functionary import utils
from functionary.config import save_config_value
from functionary.utils import (
    _get_functions_for_package,
    check_changes,
    new_functions,
    removed_element,
    updated_functions,
)


def function_creator(num):
    function_list = {}
    for i in range(num):
        function_dict = {}
        function_dict["name"] = f"Test Name{i}"
        function_dict["display_name"] = f"Test Display{i}"
        function_dict["summary"] = f"Test Summary{i}"
        function_dict["description"] = f"Test Description{i}"
        function_dict["return_type"] = f"Test Return{i}"
        function_dict["parameters"] = [
            {
                "name": f"file{i}",
                "display_name": f"display_name{i}",
                "description": f"description{i}",
                "type": f"type{i}",
                "required": "true",
            },
            {
                "name": f"file0{i}",
                "display_name": f"display_name0{i}",
                "description": f"description0{i}",
                "type": f"type0{i}",
                "required": "true",
            },
        ]
        if i == 0:
            function_list[0] = [function_dict]
        else:
            function_list[0].append(function_dict)
    return function_list


@pytest.fixture
def api_functions():
    function_list = function_creator(3)
    return function_list


@pytest.fixture
def package_with_new_functions():
    function_list = function_creator(4)
    return function_list


@pytest.fixture
def package_with_removed_functions():
    function_list = function_creator(2)
    return function_list


@pytest.fixture
def package_with_updated_functions():
    function_list = function_creator(3)
    function_list[0][1]["display_name"] = "Updated Display Name"
    function_list[0][1]["summary"] = "Updated Summary"
    return function_list


@pytest.fixture
def package_with_updated_parameters():
    function_list = function_creator(3)
    function_list[0][1]["parameters"] = [
        {
            "name": "file1",
            "display_name": "display_name1",
            "description": "description1",
            "type": "type1",
            "required": "true",
        },
        {
            "name": "file01",
            "display_name": "display_name01",
            "description": "description01_updated",
            "type": "type01",
            "required": "true",
        },
    ]
    return function_list


def response_200(*args, **kwargs):
    response = Mock()
    response.status = 200
    response.data = b"""{
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


def get_package_id_mock(packages, package_name):
    return None


def get_package_functions_mock(path):
    return {
        "name": "test",
        "display_name": "display test",
        "summary": "summary test",
        "language": "python",
        "functions": function_creator(4)[0],
    }


def get_functions_for_package_mock(name):
    return function_creator(2)[0]


def test_new_functions(package_with_new_functions, api_functions):
    """Additional function in the package that is not yet in the api"""
    result = new_functions(package_with_new_functions[0], api_functions[0])
    assert result[0].get("name") == "Test Name3"


def test_removed_functions(package_with_removed_functions, api_functions):
    """Additional function in the api that is not in the package"""
    result = removed_element(package_with_removed_functions[0], api_functions[0])
    assert result[0].get("name") == "Test Name2"


def test_updated_functions(package_with_updated_functions, api_functions):
    """Changed two fields in one of the functions in the package"""
    result = updated_functions(package_with_updated_functions[0], api_functions[0])
    assert result["Test Name1"] == ["display_name", "summary"]


def test_updated_function_parameters(package_with_updated_parameters, api_functions):
    """Changed parameters in one of the functions in the package"""
    result = updated_functions(package_with_updated_parameters[0], api_functions[0])
    assert result["Test Name1"] == ["parameters"]


def test_get_functions_for_package(monkeypatch):
    """
    Tests when there are packages in the API, but the new package isn't in the API
    """
    monkeypatch.setattr(utils, "_get_package_id", get_package_id_mock)
    monkeypatch.setattr(urllib3.PoolManager, "request", response_200)

    host = "http://test:1234"
    save_config_value("host", host)

    assert _get_functions_for_package("package_name") == {}


def test_check_changes(monkeypatch):
    """
    Tests check changes to make sure it recognizes new functions
    """
    monkeypatch.setattr(utils, "_get_package_functions", get_package_functions_mock)
    monkeypatch.setattr(
        utils, "_get_functions_for_package", get_functions_for_package_mock
    )

    assert check_changes("/arbitrary/path") is True
