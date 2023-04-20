import uuid

from django.db import models


class WorkflowRunStep(models.Model):
    """A WorkflowRunStep tracks the execution of a Task as a part of a Workflow.

    This model relates a Task to the Workflow and WorkflowStep that it is executing.
    When execution of a Workflow initially begins, all of the WorkflowRunSteps required
    to execute all of the Workflow's steps should be created. This upfront creation
    allows for the capture of important information about the step as of the time of
    execution, making it possible to accurately convey the execution of the Workflow
    even if the WorkflowSteps change at a later point in time. That is, the Workflow's
    steps can be re-ordered, removed, renamed, etc. without impacting the record of what
    the Workflow's steps looked like at the time of a specific execution.

    Attributes:
      id: The unique identifier (uuid)
      workflow_step: WorkflowStep to be executed
      step_name: The WorkflowStep name at time of execution
      step_order: The WorkflowStep's position in the Workflow at time of execution
      step_task: Task corresponding to the execution of the WorkflowStep
      workflow_task: Task corresponding to the overall Workflow execution
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_step = models.ForeignKey(
        to="WorkflowStep", blank=True, null=True, on_delete=models.SET_NULL
    )
    step_name = models.CharField(max_length=64)
    step_order = models.IntegerField()
    step_task = models.OneToOneField(
        to="Task",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="workflow_run_step",
    )
    workflow_task = models.ForeignKey(
        to="Task", on_delete=models.CASCADE, related_name="steps"
    )
