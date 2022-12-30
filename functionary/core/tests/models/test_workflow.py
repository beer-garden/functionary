import pytest

from core.models import Function, Package, Team, User, Workflow, WorkflowStep


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
    function_schema = {
        "title": "test",
        "type": "object",
        "properties": {"prop1": {"type": "integer"}},
    }
    return Function.objects.create(
        name="testfunction",
        package=package,
        schema=function_schema,
    )


@pytest.fixture
def workflow(function, environment, user):
    workflow_ = Workflow.objects.create(
        environment=environment, name="workflow", creator=user
    )

    last = WorkflowStep.objects.create(
        workflow=workflow_,
        name="last",
        function=function,
        parameter_template='{"prop1": 3}',
        next=None,
    )

    middle = WorkflowStep.objects.create(
        workflow=workflow_,
        name="middle",
        function=function,
        parameter_template='{"prop1": 2}',
        next=last,
    )

    _ = WorkflowStep.objects.create(
        workflow=workflow_,
        name="first",
        function=function,
        parameter_template='{"prop1": 1}',
        next=middle,
    )

    return workflow_


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
