from typing import TYPE_CHECKING

from django.db import transaction

from core.models import WorkflowStep

if TYPE_CHECKING:
    from core.models import Function, Workflow


def add_step(
    workflow: "Workflow",
    name: str,
    function: "Function",
    parameter_template: str,
    next: WorkflowStep | None = None,
) -> WorkflowStep:
    """Add a WorkflowStep to the specified point in the Workflow

    Args:
        workflow: Workflow to add a step to
        name: Name of the WorkflowStep
        function: Function to task
        parameter_template: Template string that will be rendered to form the
            parameter json for the function
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
            function=function,
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
