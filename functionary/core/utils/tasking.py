import logging
from uuid import UUID

from celery.utils.log import get_task_logger
from django.conf import settings

from core.celery import app
from core.models import (
    Environment,
    Function,
    ScheduledTask,
    Task,
    TaskLog,
    TaskResult,
    Workflow,
    WorkflowRunStep,
)
from core.utils.messaging import get_route, send_message
from core.utils.minio import MinioInterface, generate_filename
from core.utils.parameter import PARAMETER_TYPE

logger = get_task_logger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


class InvalidStatus(Exception):
    pass


class InvalidContentObject(Exception):
    pass


def _generate_task_message(task: Task) -> dict:
    """Generates tasking message from the provided Task"""
    variables = {var.name: var.value for var in task.variables}
    return {
        "id": str(task.id),
        "package": task.tasked_object.package.full_image_name,
        "function": task.tasked_object.name,
        "function_parameters": task.parameters,
        "variables": variables,
    }


def _protect_output(task, output):
    """Mask the values of the tasks protected variables in the output.

    Does a simple protection for variable values over 4 characters
    long. This is arbitrary, but the results are easily reversed if
    its too short.
    """
    mask = list(task.variables.filter(protect=True).values_list("value", flat=True))
    protected_output = output
    for to_mask in mask:
        if len(to_mask) > 4:
            protected_output = protected_output.replace(to_mask, "********")

    return protected_output


@app.task(
    default_retry_delay=30,
    retry_kwargs={
        "max_retries": 3,
    },
    autoretry_for=(Exception,),
)
def publish_task(task_id: UUID) -> None:
    """Publish the tasking message to the message broker so that it can be received
    and executed by a runner.

    Args:
        task_id: ID of the task to be executed
    """
    logger.debug(f"Publishing message for Task: {task_id}")

    task = (
        Task.objects.select_related("environment")
        .prefetch_related("tasked_object")
        .get(id=task_id)
    )

    _handle_file_parameters(task)

    exchange, routing_key = get_route(task)
    send_message(exchange, routing_key, "TASK_PACKAGE", _generate_task_message(task))


@app.task()
def record_task_result(task_result_message: dict) -> None:
    """Parses the task result message and generates a TaskResult entry for it

    Args:
        task_result_message: The message body from a TASK_RESULT message.
    """
    task_id = task_result_message["task_id"]
    status = task_result_message["status"]
    output = task_result_message["output"]
    result = task_result_message["result"]

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        logger.error("Unable to record results for task %s: task not found", task_id)
        return

    TaskLog.objects.create(task=task, log=_protect_output(task, output))
    TaskResult.objects.create(task=task, result=result)

    # TODO: This status determination feels like it belongs in the runner. This should
    #       be reworked so that there are explicitly known statuses that could come
    #       back from the runner, rather than passing through the command exit status
    #       as is happening now.
    _update_task_status(task, status)

    # If this task is part of a WorkflowRun continue it or update its status
    if workflow_run_step := WorkflowRunStep.objects.filter(step_task=task):
        _handle_workflow_run(workflow_run_step.get(), task)


@app.task
def run_scheduled_task(scheduled_task_id: str) -> None:
    """Creates and executes a Task according to a schedule

    Uses the given ScheduledTask object id as a string to fetch the ScheduledTask.
    The necessary metadata is taken from the ScheduledTask object to construct
    a new Task. The new Task is then associated with that ScheduledTask. The
    ScheduledTask metadata is then updated with the newly created Task.

    Args:
        scheduled_task_id: A string of the ID for the ScheduledTask object

    Returns:
        None
    """
    scheduled_task = ScheduledTask.objects.get(id=scheduled_task_id)

    task = Task.objects.create(
        environment=scheduled_task.environment,
        creator=scheduled_task.creator,
        tasked_object=scheduled_task.function,
        return_type=scheduled_task.function.return_type,
        parameters=scheduled_task.parameters,
        scheduled_task=scheduled_task,
    )

    start_task(task)
    scheduled_task.update_most_recent_task(task)


def _update_task_status(task: Task, status: int) -> None:
    match status:
        case 0:
            task.status = Task.COMPLETE
        case _:
            task.status = Task.ERROR

    task.save()

    if task.scheduled_task is not None and status == "ERROR":
        task.scheduled_task.error()


def _handle_workflow_run(workflow_run_step: WorkflowRunStep, task: Task) -> None:
    """Start the next task for a WorkflowRun or update its status as appropriate"""
    workflow_task = workflow_run_step.workflow_task

    match task.status:
        case Task.COMPLETE:
            if next_step := workflow_run_step.workflow_step.next:
                next_step.execute(workflow_task=workflow_task)
            else:
                workflow_task.complete()
        case Task.ERROR:
            workflow_task.error()


def _handle_file_parameters(task: Task) -> None:
    """Update all file parameter's filenames to presigned URLs

    This function will mutate all file parameters to their
    corresponding presigned URLs. This should only be done
    before a task is sent to the runner. The task should not
    save the presigned URL to its database entry.

    Args:
        task: The task that is about to be sent to the runner

    Returns:
        None
    """
    environment = task.environment
    parameters = task.parameters

    for parameter in task.tasked_object.parameters.filter(
        parameter_type=PARAMETER_TYPE.FILE, name__in=parameters.keys()
    ):
        param_name = parameter.name

        filename = generate_filename(task, param_name, parameters[param_name])
        parameters[param_name] = _get_presigned_url(filename, environment)


def _get_presigned_url(filename: str, environment: Environment) -> str:
    minio = MinioInterface(bucket_name=str(environment.id))
    presigned_url = minio.get_presigned_url(filename)
    return presigned_url


def _start_function_task(task: Task) -> None:
    """Publishes the task for execution"""
    publish_task.delay(task.id)


def _start_workflow_task(task: Task) -> None:
    """Starts the workflow run associated with the given task"""
    task.workflow.first_step.execute(workflow_task=task)


def start_task(task: Task) -> None:
    """Start the provided task

    Starts a Task by executing the necessary steps for its tasked_object. The task
    status will be set to PENDING and the task will be saved as part of this process.

    Args:
        task: Task to start

    Returns:
        None

    Raises:
        InvalidContentType: The tasked_object associated with the task is of an
                            unrecognized type
        InvalidStatus: The task cannot be started based on its current status
    """
    if task.status != Task.PENDING:
        raise InvalidStatus(f"Task with status f{task.status} cannot be started")

    task.in_progress()

    tasked_type_class = task.tasked_type.model_class()

    if tasked_type_class is Function:
        _start_function_task(task)
    elif tasked_type_class is Workflow:
        _start_workflow_task(task)
    else:
        raise InvalidContentObject(
            f"Handling for content type {tasked_type_class} is undefined"
        )
