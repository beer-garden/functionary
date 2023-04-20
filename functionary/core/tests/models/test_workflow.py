import pytest
from django.core.exceptions import ValidationError

from core.models import Function, Package, ScheduledTask, Task, Team, User, Workflow
from core.utils.parameter import PARAMETER_TYPE


@pytest.fixture
def user():
    return User.objects.create(username="user")


@pytest.fixture
def team():
    return Team.objects.create(name="team")


@pytest.fixture
def environment(team):
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
        active=True,
    )

    _function.parameters.create(name="prop1", parameter_type=PARAMETER_TYPE.INTEGER)

    return _function


@pytest.fixture
def workflow(function, environment, user):
    _workflow = Workflow.objects.create(
        environment=environment, name="workflow", creator=user
    )

    _workflow.parameters.create(name="wfprop1", parameter_type=PARAMETER_TYPE.INTEGER)

    last = _workflow.steps.create(
        name="last",
        tasked_object=function,
        parameter_template='{"prop1": 3}',
        next=None,
    )

    middle = _workflow.steps.create(
        name="middle",
        tasked_object=function,
        parameter_template='{"prop1": 2}',
        next=last,
    )

    _ = _workflow.steps.create(
        name="first",
        tasked_object=function,
        parameter_template='{"prop1": 1}',
        next=middle,
    )

    return _workflow


@pytest.fixture
def scheduled_task(workflow):
    return ScheduledTask.objects.create(
        tasked_object=workflow,
        environment=workflow.environment,
        creator=workflow.creator,
        parameters={},
        status=ScheduledTask.ACTIVE,
    )


@pytest.mark.django_db
def test_first_step(workflow):
    """The first step in the workflow is properly determined"""
    assert workflow.first_step == workflow.steps.get(name="first")


@pytest.mark.django_db
def test_ordered_steps(workflow):
    """Steps are returned in their proper sequence order"""
    first = workflow.steps.get(name="first")
    middle = workflow.steps.get(name="middle")
    last = workflow.steps.get(name="last")

    ordered_steps = workflow.ordered_steps

    assert ordered_steps[0] == first
    assert ordered_steps[1] == middle
    assert ordered_steps[2] == last


@pytest.mark.django_db
def test_workflow_task_parameters_validation(workflow):
    """Task with invalid parameters raises ValidationError"""
    run = Task(
        tasked_object=workflow,
        environment=workflow.environment,
        parameters={"wfprop1": "notanint"},
        creator=workflow.creator,
    )

    with pytest.raises(ValidationError):
        run.clean()


@pytest.mark.django_db
def test_deactivate(workflow, scheduled_task):
    """Deactivating a workflow pauses active scheduled tasks"""
    assert workflow.active
    assert scheduled_task.status == ScheduledTask.ACTIVE

    workflow.deactivate()
    scheduled_task.refresh_from_db()

    assert workflow.active is False
    assert scheduled_task.status == ScheduledTask.PAUSED
