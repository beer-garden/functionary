from uuid import uuid4

import pytest

from core.models import Function, Package, Task, Team, User, Workflow, WorkflowStep
from core.utils.parameter import PARAMETER_TYPE
from core.utils.workflow import (
    InvalidSteps,
    add_step,
    generate_run_steps,
    move_step,
    remove_step,
    reorder_steps,
)


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
    )

    _function.parameters.create(name="prop1", parameter_type=PARAMETER_TYPE.INTEGER)

    return _function


@pytest.fixture
def workflow(function, environment, user):
    workflow_ = Workflow.objects.create(
        environment=environment, name="workflow", creator=user
    )

    last = WorkflowStep.objects.create(
        workflow=workflow_,
        name="last",
        tasked_object=function,
        parameter_template='{"prop1": 3}',
        next=None,
    )

    middle = WorkflowStep.objects.create(
        workflow=workflow_,
        name="middle",
        tasked_object=function,
        parameter_template='{"prop1": 2}',
        next=last,
    )

    _ = WorkflowStep.objects.create(
        workflow=workflow_,
        name="first",
        tasked_object=function,
        parameter_template='{"prop1": 1}',
        next=middle,
    )

    return workflow_


@pytest.fixture
def other_workflow(function, environment, user):
    other_workflow_ = Workflow.objects.create(
        environment=environment, name="other_workflow", creator=user
    )

    _ = WorkflowStep.objects.create(
        workflow=other_workflow_,
        name="first",
        tasked_object=function,
        parameter_template='{"prop1": 99}',
        next=None,
    )

    return other_workflow_


@pytest.mark.django_db
def test_add_step_at_end(workflow, function):
    """Steps can be added to the end of the workflow"""
    new_last = add_step(
        workflow=workflow,
        name="new_last",
        tasked_object=function,
        parameter_template='{"prop1": 12}',
    )

    assert workflow.steps.count() == 4
    assert workflow.steps.get(name="new_last").next is None
    assert workflow.steps.get(name="last").next == new_last


@pytest.mark.django_db
def test_add_step_in_middle(workflow, function):
    """Steps can be added to the middle of the workflow"""
    second = add_step(
        workflow=workflow,
        name="second",
        tasked_object=function,
        parameter_template='{"prop1": 12}',
        next=workflow.steps.get(name="middle"),
    )

    assert workflow.steps.count() == 4
    assert workflow.steps.get(name="first").next == second


@pytest.mark.django_db
def test_add_step_workflow_must_match_next(workflow, other_workflow, function):
    """Workflow for next step must match workflow value"""
    with pytest.raises(ValueError):
        _ = add_step(
            workflow=workflow,
            name="new_step",
            tasked_object=function,
            parameter_template='{"prop1": 99}',
            next=other_workflow.steps.get(name="first"),
        )


@pytest.mark.django_db
def test_remove_step(workflow):
    """Steps can be removed from the workflow"""
    remove_step(workflow.steps.get(name="middle"))

    first = workflow.steps.get(name="first")
    last = workflow.steps.get(name="last")

    assert workflow.steps.count() == 2
    assert first.next == last


@pytest.mark.django_db
def test_move_step(workflow):
    """Steps can be moved to another point in the Workflow"""
    first = workflow.steps.get(name="first")
    middle = workflow.steps.get(name="middle")
    last = workflow.steps.get(name="last")

    move_step(last, first)

    first.refresh_from_db()
    middle.refresh_from_db()
    last.refresh_from_db()

    move_step(first, None)

    # New order should be last, middle, first
    ordered_steps = workflow.ordered_steps
    assert ordered_steps[0] == last
    assert ordered_steps[1] == middle
    assert ordered_steps[2] == first


@pytest.mark.django_db
def test_move_step_only_within_same_workflow(workflow, other_workflow):
    """The step to move and its new next target must be in the same Workflow"""
    with pytest.raises(ValueError):
        move_step(
            workflow.steps.get(name="first"), other_workflow.steps.get(name="first")
        )


@pytest.mark.django_db
def test_generate_run_steps(workflow):
    """WorkflowRunStep instances are properly created for a workflow task"""
    task = Task.objects.create(
        tasked_object=workflow,
        environment=workflow.environment,
        creator=workflow.creator,
        parameters={},
    )

    run_steps = generate_run_steps(task)
    workflow_steps = workflow.ordered_steps

    assert len(run_steps) == len(workflow_steps)

    for order, step in enumerate(workflow_steps):
        run_step = run_steps[order]
        assert run_step.workflow_step == step
        assert run_step.step_name == step.name
        assert run_step.step_order == order + 1


@pytest.mark.django_db
def test_reorder_step(workflow):
    """Steps can be reordered in Workflow"""
    first = workflow.steps.get(name="first")
    middle = workflow.steps.get(name="middle")
    last = workflow.steps.get(name="last")

    reorder_steps(step_ids=[last.id, middle.id, first.id], workflow=workflow)

    workflow.refresh_from_db()
    first.refresh_from_db()
    middle.refresh_from_db()
    last.refresh_from_db()

    # New order should be last, middle, first
    ordered_steps = workflow.ordered_steps
    assert ordered_steps[0] == last
    assert ordered_steps[1] == middle
    assert ordered_steps[2] == first


@pytest.mark.django_db
def test_reorder_steps_handles_multiple_changes(workflow):
    """Steps can be reordered in Workflow"""
    first = workflow.steps.get(name="first")
    middle = workflow.steps.get(name="middle")
    last = workflow.steps.get(name="last")

    reorder_steps(step_ids=[middle.id, last.id, first.id], workflow=workflow)

    workflow.refresh_from_db()
    first.refresh_from_db()
    middle.refresh_from_db()
    last.refresh_from_db()

    # New order should be middle, last, first
    ordered_steps = workflow.ordered_steps
    assert ordered_steps[0] == middle
    assert ordered_steps[1] == last
    assert ordered_steps[2] == first


@pytest.mark.django_db
def test_reorder_steps_handles_duplicate_ids(workflow):
    """Step id list can not have duplicates"""
    first = workflow.steps.get(name="first")
    middle = workflow.steps.get(name="middle")
    last = workflow.steps.get(name="last")
    with pytest.raises(InvalidSteps):
        reorder_steps(
            step_ids=[middle.id, last.id, middle.id, first.id], workflow=workflow
        )


@pytest.mark.django_db
def test_reorder_steps_handles_missing_ids(workflow):
    """Step id list needs to can not be missing any steps in Workflow"""
    first = workflow.steps.get(name="first")
    middle = workflow.steps.get(name="middle")
    with pytest.raises(InvalidSteps):
        # step_ids is missing the third step id
        reorder_steps(step_ids=[middle.id, first.id], workflow=workflow)


@pytest.mark.django_db
def test_reorder_steps_handles_extra_ids(workflow):
    """Step id list can not have any steps that are not in the Workflow"""
    first = workflow.steps.get(name="first")
    middle = workflow.steps.get(name="middle")
    last = workflow.steps.get(name="last")
    with pytest.raises(InvalidSteps):
        reorder_steps(
            step_ids=[middle.id, last.id, first.id, uuid4()], workflow=workflow
        )
