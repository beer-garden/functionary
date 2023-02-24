import json

import pytest
from django.test.client import MULTIPART_CONTENT, Client
from django.urls import reverse

from core.models import Environment, Function, Package, Task, TaskResult, Team
from core.utils.parameter import PARAMETER_TYPE


@pytest.fixture
def environment() -> Environment:
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment: Environment) -> Package:
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def int_function(package: Package) -> Function:
    _function = Function.objects.create(
        name="testfunction_int",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(name="prop1", parameter_type=PARAMETER_TYPE.INTEGER)

    return _function


@pytest.fixture
def json_function(package: Package) -> Function:
    _function = Function.objects.create(
        name="testfunction_json",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(name="prop1", parameter_type=PARAMETER_TYPE.JSON)

    return _function


@pytest.fixture
def file_function(package: Package) -> Function:
    _function = Function.objects.create(
        name="testfunction_file",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(name="prop1", parameter_type=PARAMETER_TYPE.FILE)

    return _function


@pytest.fixture
def task(int_function, admin_user) -> Task:
    return Task.objects.create(
        function=int_function,
        environment=int_function.package.environment,
        parameters={"prop1": "value1"},
        creator=admin_user,
    )


@pytest.fixture
def request_headers(environment: Environment) -> dict:
    return {"HTTP_X_ENVIRONMENT_ID": str(environment.id)}


def test_valid_content_type(
    admin_client: Client,
    int_function: Function,
    request_headers: dict,
):
    """Test for valid content types"""
    url = reverse("task-list")

    # Due to the way Django encodes a multipart payload, nested dicts do not work
    # https://code.djangoproject.com/ticket/30735
    task_input = {
        "function": str(int_function.id),
        "parameters": json.dumps({"prop1": 5}),
    }

    response = admin_client.post(
        url, data=task_input, content_type="application/json", **request_headers
    )
    assert response.status_code == 415

    response = admin_client.post(
        url, data=task_input, content_type=MULTIPART_CONTENT, **request_headers
    )
    assert response.status_code == 201


def test_create_int_task(
    admin_client: Client,
    int_function: Function,
    request_headers: dict,
):
    """Create a Task with integer parameters"""
    url = reverse("task-list")

    task_input = {
        "function": str(int_function.id),
        "parameters": json.dumps({"prop1": 5}),
    }

    response = admin_client.post(
        url, data=task_input, content_type=MULTIPART_CONTENT, **request_headers
    )
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_json_task(
    admin_client: Client,
    json_function: dict,
    request_headers: dict,
):
    """Create a Task with JSON parameters"""
    url = reverse("task-list")

    task_input = {
        "function": str(json_function.id),
        "parameters": json.dumps({"prop1": {"hello": "world"}}),
    }

    response = admin_client.post(
        url, data=task_input, content_type=MULTIPART_CONTENT, **request_headers
    )
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_file_task(
    mocker,
    admin_client: Client,
    file_function: Function,
    request_headers: dict,
):
    """Create a Task with file parameters"""

    def mock_file_upload(_task, _request):
        """Mock the method of uploading a file to S3"""
        return

    url = reverse("task-list")

    mocker.patch("core.api.v1.views.task._upload_files", mock_file_upload)

    with open("core/tests/api/v1/views/test_text.txt", "rb") as f:
        file_function_input = {"function": str(file_function.id), "prop1": f}
        response = admin_client.post(
            url,
            data=file_function_input,
            content_type=MULTIPART_CONTENT,
            **request_headers,
        )

    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_returns_400_for_invalid_parameters(
    admin_client: Client,
    int_function: Function,
    json_function: Function,
    request_headers: dict,
):
    """Return a 400 for invalid tasking parameters"""
    url = reverse("task-list")

    invalid_int_function_input = {
        "function": str(int_function.id),
        "parameters": json.dumps({"prop1": "not an integer"}),
    }
    response = admin_client.post(
        url,
        data=invalid_int_function_input,
        content_type=MULTIPART_CONTENT,
        **request_headers,
    )

    assert response.status_code == 400
    assert not Task.objects.filter(function=int_function).exists()

    invalid_json_input = {
        "function": json_function,
        "parameters": '{"hello": "world"',
    }

    # Wrap in 'raises' to avoid Django encode_multipart JSON decode exception
    with pytest.raises(json.JSONDecodeError):
        response = admin_client.post(
            url,
            data=invalid_json_input,
            content_type=MULTIPART_CONTENT,
            **request_headers,
        )
        assert response.status_code == 400
        assert not Task.objects.filter(function=json_function).exists()


def test_no_result_returns_404(admin_client: Client, task: Task, request_headers: dict):
    """The task result is returned as the correct type"""

    url = f"{reverse('task-list')}{task.id}/result/"
    response = admin_client.get(url, **request_headers)

    assert response.status_code == 404


def test_result_type_is_preserved(
    admin_client: Client, task: Task, request_headers: dict
):
    """The task result is returned as the correct type"""
    url = f"{reverse('task-list')}{task.id}/result/"

    str_result = json.dumps("1234")
    int_result = json.dumps(1234)
    list_result = json.dumps([1, 2, 3, 4])
    dict_result = json.dumps({"one": 1, "two": 2, "three": 3, "four": 4})
    bool_result = json.dumps(True)

    task_result = TaskResult.objects.create(task=task)

    task_result.result = str_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is str

    task_result.result = int_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is int

    task_result.result = list_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is list

    task_result.result = dict_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is dict

    task_result.result = bool_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is bool
