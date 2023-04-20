import json

import pytest
from django.core.files.base import ContentFile
from django.test.client import MULTIPART_CONTENT, Client
from django.urls import reverse
from rest_framework.test import APIClient

from core.auth import Role
from core.models import (
    Environment,
    EnvironmentUserRole,
    Function,
    Package,
    Task,
    TaskResult,
    Team,
    User,
    UserFile,
    Workflow,
    WorkflowParameter,
    WorkflowStep,
)
from core.models.package import PACKAGE_STATUS
from core.utils.parameter import PARAMETER_TYPE


@pytest.fixture()
def admin_client(admin_user) -> APIClient:
    """Custom admin_client fixture built on DRF APIClient"""
    client = APIClient()
    client.force_authenticate(user=admin_user)

    return client


@pytest.fixture
def user(environment):
    user_ = User.objects.create(username="testuser")

    EnvironmentUserRole.objects.create(
        user=user_,
        environment=environment,
        role=Role.DEVELOPER.name,
    )

    return user_


@pytest.fixture
def environment() -> Environment:
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment: Environment) -> Package:
    return Package.objects.create(
        name="testpackage", environment=environment, status=PACKAGE_STATUS.ACTIVE
    )


@pytest.fixture
def personal_file(environment, admin_user):
    user_file = UserFile(
        environment=environment, creator=admin_user, name="personal_file", public=False
    )
    user_file.file.save(user_file.name, ContentFile("personal file"))

    return user_file


@pytest.fixture
def private_file_of_another_user(environment):
    user = User.objects.create(username="another_user")
    user_file = UserFile(
        environment=environment, creator=user, name="private_file", public=False
    )
    user_file.file.save(user_file.name, ContentFile("private test file"))

    return user_file


@pytest.fixture
def function(package: Package) -> Function:
    _function = Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(name="int_param", parameter_type=PARAMETER_TYPE.INTEGER)
    _function.parameters.create(name="str_param", parameter_type=PARAMETER_TYPE.STRING)
    _function.parameters.create(name="json_param", parameter_type=PARAMETER_TYPE.JSON)
    _function.parameters.create(name="file_param", parameter_type=PARAMETER_TYPE.FILE)
    _function.parameters.create(
        name="options_param",
        parameter_type=PARAMETER_TYPE.STRING,
        options=["option1", "option2"],
    )

    return _function


@pytest.fixture
def task(function, admin_user) -> Task:
    return Task.objects.create(
        tasked_object=function,
        environment=function.package.environment,
        parameters={"int_param": 1},
        creator=admin_user,
    )


@pytest.fixture
def task2(function, user) -> Task:
    return Task.objects.create(
        tasked_object=function,
        environment=function.package.environment,
        parameters={"int_param": 1},
        status="COMPLETE",
        creator=user,
    )


@pytest.fixture
def all_tasks(task, task2):
    return [task, task2]


@pytest.fixture
def request_headers(environment: Environment) -> dict:
    return {"X-Environment-Id": str(environment.id)}


@pytest.fixture
def workflow(function: Function, admin_user) -> Workflow:
    _workflow = Workflow.objects.create(
        environment=function.environment, name="workflow", creator=admin_user
    )

    WorkflowParameter.objects.create(
        workflow=_workflow, name="int_param", parameter_type=PARAMETER_TYPE.INTEGER
    )

    WorkflowStep.objects.create(
        workflow=_workflow,
        name="step1",
        next=None,
        tasked_object=function,
        parameter_template='{"int_param": {{parameters.int_param}}}',
    )

    return _workflow


def test_create_int_task(
    admin_client: Client,
    function: Function,
    request_headers: dict,
):
    """Create a Task with integer parameters by Function ID"""
    url = reverse("task-list")

    task_input = {
        "function": str(function.id),
        "parameters": {"int_param": 5},
    }

    response = admin_client.post(url, data=task_input, headers=request_headers)
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_task_by_name(
    admin_client: Client,
    function: Function,
    package: Package,
    request_headers: dict,
):
    """Create a Task by Function name"""
    url = reverse("task-list")

    task_input = {
        "function_name": function.name,
        "package_name": package.name,
        "parameters": {"int_param": 5},
    }

    response = admin_client.post(url, data=task_input, headers=request_headers)
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_json_task(
    admin_client: Client,
    function: Function,
    request_headers: dict,
):
    """Create a Task with JSON parameters"""
    url = reverse("task-list")

    task_input = {
        "function": str(function.id),
        "parameters": {"json_param": {"hello": "world"}},
    }

    response = admin_client.post(url, data=task_input, headers=request_headers)
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_file_task(
    admin_client: Client,
    function: Function,
    request_headers: dict,
    personal_file: UserFile,
):
    """Create a Task with file parameters"""

    url = reverse("task-list")

    task_input = {
        "function": str(function.id),
        "parameters": {"file_param": str(personal_file.id)},
    }
    response = admin_client.post(
        url,
        data=task_input,
        headers=request_headers,
    )

    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_return_400_for_file_task_with_invalid_file_id_format(
    admin_client: Client,
    function: Function,
    request_headers: dict,
):
    """Create a Task with a file parameter that is not a valid UUID returns 400"""

    url = reverse("task-list")

    task_input = {
        "function": str(function.id),
        "parameters": {"file_param": 12},
    }
    response = admin_client.post(
        url,
        data=task_input,
        headers=request_headers,
    )

    assert response.status_code == 400


def test_create_return_400_for_file_task_with_other_users_private_file(
    admin_client: Client,
    function: Function,
    request_headers: dict,
    private_file_of_another_user: UserFile,
):
    """Create a Task with a file parameter that is private and owned by another user
    returns a 400"""

    url = reverse("task-list")

    task_input = {
        "function": str(function.id),
        "parameters": {"file_param": str(private_file_of_another_user.id)},
    }
    response = admin_client.post(
        url,
        data=task_input,
        headers=request_headers,
    )

    assert response.status_code == 400
    assert "does not exist" in response.content.decode()


def test_create_returns_415_for_invalid_content_type(
    admin_client: Client,
    function: Function,
    request_headers: dict,
):
    """Test for valid content types"""
    url = reverse("task-list")

    task_input = {
        "function": str(function.id),
        "parameters": {"int_param": 5},
    }

    response = admin_client.post(
        url, data=task_input, content_type=MULTIPART_CONTENT, headers=request_headers
    )
    assert response.status_code == 415


def test_create_returns_400_for_extra_parameters(
    admin_client: Client,
    function: Function,
    request_headers: dict,
):
    """Return a 400 if additional, unexpected parameters are provided"""
    url = reverse("task-list")

    input_with_extra_parameters = {
        "function": str(function.id),
        "parameters": {"int_param": 5, "unexpected_param": 12},
    }

    response = admin_client.post(
        url,
        data=input_with_extra_parameters,
        headers=request_headers,
    )

    assert response.status_code == 400
    assert "unexpected_param" in response.content.decode()
    assert not Task.objects.filter(tasked_id=function.id).exists()


def test_create_returns_400_for_invalid_int_parameters(
    admin_client: Client,
    function: Function,
    request_headers: dict,
):
    """Return a 400 for invalid int parameters"""
    url = reverse("task-list")

    invalid_function_input = {
        "function": str(function.id),
        "parameters": {"int_param": "not an integer"},
    }

    response = admin_client.post(
        url,
        data=invalid_function_input,
        headers=request_headers,
    )

    assert response.status_code == 400
    assert "int_param" in response.content.decode()
    assert not Task.objects.filter(tasked_id=function.id).exists()


def test_create_returns_400_for_invalid_function_name(
    admin_client: Client,
    package: Package,
    request_headers: dict,
):
    """Return a 400 for invalid function name"""
    url = reverse("task-list")

    task_input = {
        "function_name": "invalid_function_name",
        "package_name": package.name,
        "parameters": {"someparam": "some_value"},
    }

    response = admin_client.post(url, data=task_input, headers=request_headers)

    assert response.status_code == 400
    assert "Invalid function" in response.json()[0]


def test_create_returns_400_for_invalid_function_id(
    admin_client: Client,
    request_headers: dict,
):
    """Return a 400 for invalid function id"""
    url = reverse("task-list")

    task_input = {
        "function": "not a uuid",
        "parameters": {"someparam": "somevalue"},
    }

    response = admin_client.post(url, data=task_input, headers=request_headers)
    assert response.status_code == 400
    assert "Invalid function" in response.json()[0]


def test_create_returns_400_for_missing_required_parameters(
    admin_client: Client,
    function: Function,
    request_headers: dict,
):
    """Return a 400 for missing required parameters"""
    url = reverse("task-list")

    function.parameters.create(
        name="required_param", parameter_type=PARAMETER_TYPE.STRING, required=True
    )

    task_input = {
        "function_name": function.name,
        "package_name": function.package.name,
        "parameters": {},
    }

    response = admin_client.post(url, data=task_input, headers=request_headers)

    assert response.status_code == 400
    assert "required_param" in response.content.decode()


def test_no_result_returns_404(admin_client: Client, task: Task, request_headers: dict):
    """The task result is returned as the correct type"""

    url = f"{reverse('task-list')}{task.id}/result/"
    response = admin_client.get(url, headers=request_headers)

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

    task_result.save_result(str_result)
    response = admin_client.get(url, headers=request_headers)
    assert type(response.data["result"]) is str

    task_result.save_result(int_result)
    response = admin_client.get(url, headers=request_headers)
    assert type(response.data["result"]) is int

    task_result.save_result(list_result)
    response = admin_client.get(url, headers=request_headers)
    assert type(response.data["result"]) is list

    task_result.save_result(dict_result)
    response = admin_client.get(url, headers=request_headers)
    assert type(response.data["result"]) is dict

    task_result.save_result(bool_result)
    response = admin_client.get(url, headers=request_headers)
    assert type(response.data["result"]) is bool


def test_workflow_task(admin_client, request_headers: dict, workflow: Workflow):
    """Create a Task for a Workflow"""
    url = reverse("task-list")

    assert not workflow.tasks.exists()

    task_input = {
        "workflow": str(workflow.id),
        "parameters": {"int_param": 5},
    }

    response = admin_client.post(
        url,
        data=task_input,
        headers=request_headers,
    )

    assert response.status_code == 201
    assert workflow.tasks.exists()


def test_create_task_with_comment(
    admin_client, request_headers: dict, function: Function
):
    """A comment can be set on the Task"""
    url = reverse("task-list")

    comment = "This is my comment."
    task_input = {
        "function": str(function.id),
        "parameters": {"int_param": 5},
        "comment": comment,
    }

    response = admin_client.post(url, data=task_input, headers=request_headers)
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.get(id=task_id).comment == comment


def test_filterset_id(admin_client, all_tasks, request_headers: dict):
    """Filter by task_id"""
    url = reverse("task-list")
    task = all_tasks[0]
    response = admin_client.get(
        url,
        data={"id": task.id},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(task.id)


def test_filterset_status(admin_client, all_tasks, request_headers: dict):
    """Filter by task_status"""
    url = reverse("task-list")
    task = all_tasks[0]
    response = admin_client.get(
        url,
        data={"status": "PENDING"},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(task.id)


def test_filterset_creator(admin_client, all_tasks, admin_user, request_headers: dict):
    """Filter by task_creator"""
    url = reverse("task-list")
    task = all_tasks[0]
    response = admin_client.get(
        url,
        data={"creator": admin_user.id},
        headers=request_headers,
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(task.id)


def test_create_options_task(
    admin_client: Client,
    function: Function,
    request_headers: dict,
):
    """Create a Task with options parameters by Function ID"""
    url = reverse("task-list")

    task_input = {
        "function": str(function.id),
        "parameters": {"options_param": "option1"},
    }

    response = admin_client.post(url, data=task_input, headers=request_headers)
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_returns_400_options_task_with_invalid_choice(
    admin_client: Client,
    function: Function,
    request_headers: dict,
):
    """Create a Task with options parameters with an invalid option by Function ID"""
    url = reverse("task-list")

    task_input = {
        "function": str(function.id),
        "parameters": {"options_param": "option5"},
    }

    response = admin_client.post(url, data=task_input, headers=request_headers)

    assert response.status_code == 400
    assert "options_param" in response.content.decode()
    assert not Task.objects.filter(tasked_id=function.id).exists()
