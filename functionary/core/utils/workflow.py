from typing import TYPE_CHECKING, List, Union
from uuid import UUID

from django.db import transaction
from django.db.models import Case, When

from core.models import WorkflowRunStep, WorkflowStep

if TYPE_CHECKING:
    from core.models import Function, Task, Workflow


class InvalidSteps(Exception):
    pass


def add_step(
    workflow: "Workflow",
    name: str,
    tasked_object: Union["Function", "Workflow"],
    parameter_template: str,
    next: WorkflowStep | None = None,
) -> WorkflowStep:
    """Add a WorkflowStep to the specified point in the Workflow

    Args:
        workflow: Workflow to add a step to
        name: Name of the WorkflowStep
        tasked_object: The Function or Workflow to task
        parameter_template: Template string that will be rendered to form the
            parameter json for the tasked object
        next: The WorkflowStep to insert the new step before. The default value
            of None will insert at the end of the Workflow.

    Returns:
        The created WorkflowStep

    Raises:
        ValueError: workflow and next.workflow do not match
    """
    if next is not None and workflow != next.workflow:
        raise ValueError("Provided next step is not part of provided workflow")

    before_step = WorkflowStep.objects.filter(workflow=workflow, next=next).first()

    with transaction.atomic():
        new_step = WorkflowStep.objects.create(
            workflow=workflow,
            name=name,
            tasked_object=tasked_object,
            parameter_template=parameter_template,
            next=before_step.next if before_step else None,
        )

        if before_step:
            before_step.next = new_step
            before_step.save()

    return new_step


def remove_step(step: WorkflowStep) -> None:
    """Remove a WorkflowStep from a Workflow

    Args:
        step: The WorkflowStep to remove

    Returns:
        None
    """
    before = WorkflowStep.objects.filter(next=step).first()

    with transaction.atomic():
        if before:
            before.next = step.next
            before.save()

        step.delete()


def reorder_steps(step_ids: List[UUID], workflow: "Workflow") -> None:
    """Reorders WorkflowSteps to match the order of step_ids

    Args:
        step_ids: A list of WorkflowStep ids
        workflow_pk: Workflow pk of that the step_ids are accosiated with

    Returns:
        None

    Raises:
        InvalidSteps: Provided step ids do not match workflow steps
    """
    step: WorkflowStep = None
    steps = WorkflowStep.objects.filter(workflow=workflow, pk__in=step_ids)

    step_order = Case(*[When(id=id, then=pos) for pos, id in enumerate(step_ids)])
    steps = workflow.steps.filter(id__in=step_ids).order_by(step_order)

    ordered_steps = workflow.ordered_steps
    if set(steps) != set(ordered_steps) or len(step_ids) != len(ordered_steps):
        raise InvalidSteps("Provided step ids do not match workflow steps")

    with transaction.atomic():
        max_index = len(steps) - 1
        for index, step in enumerate(steps):
            step.next = steps[index + 1] if index != max_index else None
            step.save()


def move_step(step: WorkflowStep, next: WorkflowStep | None = None) -> None:
    """Move a WorkflowStep to a different point in the Workflow

    Args:
        step: The WorkflowStep to move
        next: WorkflowStep to place step before in the Workflow. Must be a member of
            the same Workflow as step. A value of None puts step at the end of the
            Workflow.

    Returns:
        None

    Raises:
        ValueError: The provided steps are not part of the same Workflow
    """
    if next is not None and step.workflow != next.workflow:
        raise ValueError("Provided step must be a member of the same Workflow")

    with transaction.atomic():
        if old_before_step := WorkflowStep.objects.filter(
            workflow=step.workflow, next=step
        ).first():
            old_before_step.next = step.next
            old_before_step.save()

        if new_before_step := WorkflowStep.objects.filter(
            workflow=step.workflow, next=next
        ).first():
            new_before_step.next = step
            new_before_step.save()

        step.next = next
        step.save()


def generate_run_steps(task: "Task") -> List[WorkflowRunStep]:
    """Generates the WorkflowRunStep instances for an execution of a Workflow.

    Args:
        task: Task for the execution of a Workflow

    Returns:
        The list of WorkflowRunSteps that were created
    """
    workflow = task.workflow
    run_steps = []

    for order, step in enumerate(workflow.ordered_steps):
        run_steps.append(
            WorkflowRunStep.objects.create(
                workflow_step=step,
                step_name=step.name,
                step_order=order + 1,
                step_task=None,
                workflow_task=task,
            )
        )

    return run_steps
