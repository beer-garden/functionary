from uuid import uuid4

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils.html import escape

from core.auth import Role
from core.models import (
    EnvironmentUserRole,
    Function,
    Package,
    Team,
    User,
    Workflow,
    WorkflowStep,
)
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
    _function = Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(name="int_param", parameter_type=PARAMETER_TYPE.INTEGER)
    _function.parameters.create(name="json_param", parameter_type=PARAMETER_TYPE.JSON)

    return _function


@pytest.fixture
def user_with_access(environment):
    user_obj = User.objects.create(username="hasaccess")

    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.ADMIN.name, environment=environment
    )

    return user_obj


@pytest.fixture
def user_without_access():
    return User.objects.create(username="noaccess")


@pytest.fixture
def workflow(environment, user_with_access):
    return Workflow.objects.create(
        environment=environment, name="testworkflow", creator=user_with_access
    )


@pytest.fixture
def step3(workflow, function):
    return WorkflowStep.objects.create(
        workflow=workflow,
        name="step3",
        tasked_object=function,
        parameter_template='{"int_param": 42}',
    )


@pytest.fixture
def step2(step3, workflow, function):
    return WorkflowStep.objects.create(
        workflow=workflow,
        name="step2",
        tasked_object=function,
        parameter_template='{"int_param": 42}',
        next=step3,
    )


@pytest.fixture
def json_parameter_value():
    return '{"number": 42}'


@pytest.fixture
def step1(step2, workflow, function, json_parameter_value):
    return WorkflowStep.objects.create(
        workflow=workflow,
        name="step1",
        tasked_object=function,
        parameter_template="{" + '"json_param": ' + json_parameter_value + "}",
        next=step2,
    )


@pytest.mark.django_db
def test_move_workflow_step(client, user_with_access, workflow, step1, step2, step3):
    client.force_login(user_with_access)

    url = reverse(
        "ui:workflowstep-move", kwargs={"workflow_pk": workflow.pk, "pk": step1.pk}
    )
    response = client.post(url, {"next": step3.pk})

    assert response.status_code == 200

    # New order should be step2, step1, step3
    steps = workflow.ordered_steps
    assert steps[0] == step2
    assert steps[1] == step1
    assert steps[2] == step3


@pytest.mark.django_db
def test_move_workflow_step_returns_400_for_invalid_next_value(
    client, user_with_access, workflow, step1
):
    client.force_login(user_with_access)

    url = reverse(
        "ui:workflowstep-move", kwargs={"workflow_pk": workflow.pk, "pk": step1.pk}
    )
    response = client.post(url, {"next": uuid4()})

    assert response.status_code == 400


@pytest.mark.django_db
def test_move_workflow_step_returns_403_for_no_access(
    client, user_without_access, workflow, step1, step3
):
    client.force_login(user_without_access)

    url = reverse(
        "ui:workflowstep-move", kwargs={"workflow_pk": workflow.pk, "pk": step1.pk}
    )
    response = client.post(url, {"next": step3.pk})

    assert response.status_code == 403


@pytest.mark.django_db
def test_move_workflow_step_returns_404_when_not_found(client, user_with_access):
    client.force_login(user_with_access)

    url = reverse(
        "ui:workflowstep-move", kwargs={"workflow_pk": uuid4(), "pk": uuid4()}
    )
    response = client.post(url, {"next": uuid4()})

    assert response.status_code == 404


@pytest.mark.django_db
def test_json_parameter_values_render_correctly_on_edit_form(
    client, user_with_access, workflow, step1, json_parameter_value
):
    client.force_login(user_with_access)

    session = client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    url = reverse(
        "ui:workflowstep-update", kwargs={"workflow_pk": workflow.pk, "pk": step1.pk}
    )
    response = client.get(url)

    assert escape(json_parameter_value) in response.rendered_content


@pytest.mark.django_db
def test_duplicate_name_fails(mocker, admin_client, workflow, step1, step2):
    """Make sure the unique constraint runs on the form validation"""

    session = admin_client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    url = reverse(
        "ui:workflowstep-update", kwargs={"workflow_pk": workflow.pk, "pk": step1.pk}
    )

    data = {
        "name": step2.name,
        "environment": workflow.environment.id,
        "tasked_id": step2.tasked_id,
        "tasked_type": "function",
    }

    response = admin_client.post(
        url,
        data=data,
    )
    assert response is not None
    assert response.status_code == 200
    assert "Workflow step with this Workflow and Name already exists" in str(
        response.content
    )


@pytest.mark.django_db
def test_reorder_workflow_steps(
    client, user_with_access, workflow, step1, step2, step3
):
    client.force_login(user_with_access)

    url = reverse("ui:workflowsteps-reorder", kwargs={"workflow_pk": workflow.pk})
    response = client.post(url, {"step_ids": [step3.id, step1.id, step2.id]})

    assert response.status_code == 200

    # New order should be step3, step1, step2
    steps = workflow.ordered_steps
    assert steps[0] == step3
    assert steps[1] == step1
    assert steps[2] == step2


@pytest.mark.django_db
def test_reorder_workflow_steps_error(
    client, user_with_access, workflow, step1, step2, step3
):
    client.force_login(user_with_access)

    url = reverse("ui:workflowsteps-reorder", kwargs={"workflow_pk": workflow.pk})
    response = client.post(url, {"step_ids": [step3.id, step1.id, step2.id, step2.id]})

    assert response.status_code == 200

    all_messages = get_messages(response.wsgi_request)
    message = ""
    for msg in all_messages:
        message = msg.message

    assert "Sorry, something went wrong! Please try again." == message
