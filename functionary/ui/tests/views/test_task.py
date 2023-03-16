"""Test Task views"""
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from core.models import Function, Package, Task, Team, Workflow

if TYPE_CHECKING:
    from django.test.client import Client

    from core.models import Environment


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def function(package):
    return Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
    )


@pytest.fixture
def workflow(environment, admin_user):
    return Workflow.objects.create(
        name="testworkflow",
        environment=environment,
        creator=admin_user,
    )


@pytest.fixture
def function_task(function, admin_user):
    return Task.objects.create(
        tasked_object=function,
        environment=function.environment,
        creator=admin_user,
        parameters={},
    )


@pytest.fixture
def workflow_task(workflow, admin_user):
    return Task.objects.create(
        tasked_object=workflow,
        environment=workflow.environment,
        creator=admin_user,
        parameters={},
    )


def test_task_list(
    admin_client: "Client",
    environment: "Environment",
    function_task: Task,
    workflow_task: Task,
):
    """task-list shows Tasks of Functions and Workflows"""
    session = admin_client.session
    session["environment_id"] = str(environment.id)
    session.save()

    url = reverse("ui:task-list")

    response = admin_client.get(url)
    response_body = response.content.decode()

    assert str(function_task.id) in response_body
    assert str(workflow_task.id) in response_body


def test_task_list_filter_by_tasked_type(
    admin_client: "Client",
    environment: "Environment",
    function_task: Task,
    workflow_task: Task,
):
    """task-list can be filtered by tasked_type"""
    session = admin_client.session
    session["environment_id"] = str(environment.id)
    session.save()

    url = reverse("ui:task-list")

    response = admin_client.get(url, data={"type": "function"})
    response_body = response.content.decode()

    assert str(function_task.id) in response_body
    assert str(workflow_task.id) not in response_body

    response = admin_client.get(url, data={"type": "workflow"})
    response_body = response.content.decode()

    assert str(function_task.id) not in response_body
    assert str(workflow_task.id) in response_body


def test_task_list_filter_by_name(
    admin_client: "Client",
    environment: "Environment",
    function_task: Task,
    workflow_task: Task,
):
    """task-list shows Tasks of Functions and Workflows"""
    session = admin_client.session
    session["environment_id"] = str(environment.id)
    session.save()

    url = reverse("ui:task-list")

    response = admin_client.get(url, data={"name": "test"})
    response_body = response.content.decode()

    assert str(function_task.id) in response_body
    assert str(workflow_task.id) in response_body

    response = admin_client.get(url, data={"name": "testfu"})
    response_body = response.content.decode()

    assert str(function_task.id) in response_body
    assert str(workflow_task.id) not in response_body
