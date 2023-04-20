"""Tests ScheduledTask views"""

import pytest
from django.test.client import Client
from django.urls import reverse

from core.models import Function, FunctionParameter, Package, ScheduledTask, Team, User
from core.models.package import PACKAGE_STATUS
from core.utils.parameter import PARAMETER_TYPE


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(
        name="testpackage", environment=environment, status=PACKAGE_STATUS.ACTIVE
    )


@pytest.fixture
def user():
    return User.objects.create(username="user")


@pytest.fixture
def function(package):
    function_ = Function.objects.create(
        name="testfunction_file",
        package=package,
        environment=package.environment,
    )

    return function_


@pytest.fixture
def required_str_parameter(function: Function):
    return function.parameters.create(
        name="required_str_param", parameter_type=PARAMETER_TYPE.STRING, required=True
    )


@pytest.fixture
def optional_file_parameter(function: Function):
    return function.parameters.create(
        name="optional_file_param", parameter_type=PARAMETER_TYPE.FILE, required=False
    )


@pytest.fixture
def optional_int_parameter(function: Function):
    return function.parameters.create(
        name="optional_int_param", parameter_type=PARAMETER_TYPE.INTEGER, required=False
    )


@pytest.fixture
def scheduled_task(user: User, function: Function):
    return ScheduledTask.objects.create(
        name="schedule1",
        environment=function.environment,
        tasked_object=function,
        creator=user,
        status=ScheduledTask.PAUSED,
    )


@pytest.mark.django_db
def test_create_excludes_empty_optional_parameters(
    admin_client: Client,
    function: Function,
    required_str_parameter: FunctionParameter,
    optional_int_parameter: FunctionParameter,
):
    """Optional parameters that are empty when the form is submitted should be excluded
    from the Task parameters"""
    url = reverse("ui:scheduledtask-create")

    session = admin_client.session
    session["environment_id"] = str(function.environment.id)
    session.save()

    required_param_name = f"task-parameter-{required_str_parameter.name}"

    data = {
        "name": "name",
        "description": "",
        "scheduled_minute": "5",
        "scheduled_hour": "5",
        "scheduled_day_of_month": "5",
        "scheduled_month_of_year": "5",
        "scheduled_day_of_week": "5",
        "tasked_type": "function",
        "tasked_id": str(function.id),
        required_param_name: "some string",
    }

    response = admin_client.post(url, data=data)

    task = ScheduledTask.objects.get(tasked_id=function.id)

    assert response.status_code == 302
    assert required_str_parameter.name in task.parameters
    assert optional_int_parameter.name not in task.parameters


@pytest.mark.django_db
def test_update_excludes_empty_optional_parameters(
    admin_client: Client,
    function: Function,
    scheduled_task: ScheduledTask,
    required_str_parameter: FunctionParameter,
    optional_int_parameter: FunctionParameter,
):
    """Optional parameters that are empty when the form is submitted should be excluded
    from the Task parameters"""
    url = reverse("ui:scheduledtask-update", kwargs={"pk": str(scheduled_task.id)})

    session = admin_client.session
    session["environment_id"] = str(function.environment.id)
    session.save()

    required_param_name = f"task-parameter-{required_str_parameter.name}"

    data = {
        "name": "name",
        "description": "",
        "scheduled_minute": "5",
        "scheduled_hour": "5",
        "scheduled_day_of_month": "5",
        "scheduled_month_of_year": "5",
        "scheduled_day_of_week": "5",
        "status": ScheduledTask.ACTIVE,
        required_param_name: "some string",
    }

    response = admin_client.post(url, data=data)

    scheduled_task.refresh_from_db()

    assert response.status_code == 302
    assert required_str_parameter.name in scheduled_task.parameters
    assert optional_int_parameter.name not in scheduled_task.parameters


@pytest.mark.django_db
def test_update_status(admin_client: Client, scheduled_task: ScheduledTask):
    new_status = ScheduledTask.ARCHIVED
    assert scheduled_task.status != new_status

    session = admin_client.session
    session["environment_id"] = str(scheduled_task.environment.id)
    session.save()

    url = reverse("ui:scheduledtask-update-status", kwargs={"pk": scheduled_task.id})
    response = admin_client.post(url, {"status": new_status})

    assert response.status_code == 302
    scheduled_task.refresh_from_db()

    assert scheduled_task.status == new_status


@pytest.mark.django_db
def test_update_status_returns_400(admin_client: Client, scheduled_task: ScheduledTask):
    new_status = "invalid_status"

    session = admin_client.session
    session["environment_id"] = str(scheduled_task.environment.id)
    session.save()

    url = reverse("ui:scheduledtask-update-status", kwargs={"pk": scheduled_task.id})
    response = admin_client.post(url, {"status": new_status})

    assert response.status_code == 400
