import uuid

from django.db import models


class WorkflowRunStep(models.Model):
    """A WorkflowRunStep tracks the run of a Task as a part of a
    Workflow"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.OneToOneField(
        to="Task", on_delete=models.PROTECT, related_name="workflow_run_step"
    )
    workflow_step = models.ForeignKey(
        to="WorkflowStep", blank=True, null=True, on_delete=models.SET_NULL
    )
    workflow_run = models.ForeignKey(
        to="WorkflowRun",
        on_delete=models.CASCADE,
        related_name="steps",
    )
