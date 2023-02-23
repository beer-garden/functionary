"""Tests function views"""

import pytest
from django.urls import reverse

from core.models import Function, Package, Task, Team
from core.utils.parameter import PARAMETER_TYPE


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
def integer_parameter(function):
    return function.parameters.create(
        name="optional_integer", parameter_type=PARAMETER_TYPE.INTEGER, required=False
    )


@pytest.fixture
def string_parameter(function):
    return function.parameters.create(
        name="optional_string", parameter_type=PARAMETER_TYPE.STRING, required=False
    )


@pytest.mark.django_db
def test_execute_handles_optional_parameters(
    admin_client, function, integer_parameter, string_parameter
):
    """Optional parameters that are empty when the form is submitted should be excluded
    from the Task parameters"""
    session = admin_client.session
    session["environment_id"] = str(function.environment.id)
    session.save()

    url = reverse("ui:function-execute")
    data = {
        "function_id": str(function.id),
        f"task-parameter-{integer_parameter.name}": "",
        f"task-parameter-{string_parameter.name}": "",
    }

    admin_client.post(url, data)
    task = Task.objects.get(function=function)

    assert integer_parameter.name not in task.parameters
    assert string_parameter.name not in task.parameters
