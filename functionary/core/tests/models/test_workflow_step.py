import pytest

from core.models import Function, Package, Task, Team, User, Workflow
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

    _function.parameters.create(
        name="func_int_param", parameter_type=PARAMETER_TYPE.INTEGER
    )

    _function.parameters.create(
        name="func_json_param", parameter_type=PARAMETER_TYPE.JSON
    )

    _function.parameters.create(
        name="func_str_param", parameter_type=PARAMETER_TYPE.STRING
    )

    return _function


@pytest.fixture
def workflow(environment, user):
    _workflow = Workflow.objects.create(
        environment=environment, name="workflow", creator=user
    )

    _workflow.parameters.create(
        name="wf_json_param", parameter_type=PARAMETER_TYPE.JSON
    )

    _workflow.parameters.create(
        name="wf_int_param", parameter_type=PARAMETER_TYPE.INTEGER
    )

    _workflow.parameters.create(
        name="wf_str_param", parameter_type=PARAMETER_TYPE.STRING
    )

    return _workflow


@pytest.mark.django_db
def test_workflow_step_generates_correct_task_parameters_for_int(workflow, function):
    """Integer workflow parameters are correctly translated to Task parameters"""
    parameter_template = '{"func_int_param": {{parameters.wf_int_param}}}'

    workflow_step = workflow.steps.create(
        name="step1",
        function=function,
        parameter_template=parameter_template,
    )

    workflow_task_params = {"wf_int_param": 10}

    workflow_task = Task.objects.create(
        tasked_object=workflow,
        creator=workflow.creator,
        environment=workflow.environment,
        parameters=workflow_task_params,
    )

    step_task = workflow_step.execute(workflow_task)

    assert (
        step_task.parameters["func_int_param"] == workflow_task_params["wf_int_param"]
    )


@pytest.mark.django_db
def test_workflow_step_generates_correct_task_parameters_for_json(workflow, function):
    """JSON workflow parameters are correctly translated to Task parameters"""
    parameter_template = '{"func_json_param": {"nested": {{parameters.wf_json_param}}}}'

    workflow_step = workflow.steps.create(
        name="step1",
        function=function,
        parameter_template=parameter_template,
    )

    workflow_task_params = {"wf_json_param": {"this": "is a test"}}

    workflow_task = Task.objects.create(
        tasked_object=workflow,
        creator=workflow.creator,
        environment=workflow.environment,
        parameters=workflow_task_params,
    )

    step_task = workflow_step.execute(workflow_task)

    assert (
        step_task.parameters["func_json_param"]["nested"]
        == workflow_task_params["wf_json_param"]
    )


@pytest.mark.django_db
def test_workflow_step_generates_correct_task_parameters_for_str(workflow, function):
    """String workflow parameters are correctly translated to Task parameters"""
    parameter_template = (
        '{"func_str_param": "fun quote: \\"{{parameters.wf_str_param}}\\""}'
    )

    workflow_step = workflow.steps.create(
        name="step1",
        function=function,
        parameter_template=parameter_template,
    )

    quote = "This is the quote"
    workflow_task_params = {"wf_str_param": quote}

    workflow_task = Task.objects.create(
        tasked_object=workflow,
        creator=workflow.creator,
        environment=workflow.environment,
        parameters=workflow_task_params,
    )

    step_task = workflow_step.execute(workflow_task)

    assert step_task.parameters["func_str_param"] == f'fun quote: "{quote}"'
