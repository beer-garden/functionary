import uuid

from django.db import models


class WorkflowRunStep(models.Model):
    """A WorkflowRunStep tracks the execution of a Task as a part of a Workflow"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_step = models.ForeignKey(
        to="WorkflowStep", blank=True, null=True, on_delete=models.SET_NULL
    )
    step_task = models.OneToOneField(
        to="Task", on_delete=models.PROTECT, related_name="workflow_run_step"
    )
    workflow_task = models.ForeignKey(
        to="Task", on_delete=models.CASCADE, related_name="steps"
    )
