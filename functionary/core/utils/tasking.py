import logging
from uuid import UUID

from celery import Task as CeleryTask
from celery.exceptions import Reject
from celery.utils.log import get_task_logger
from django.conf import settings

from core.celery import app
from core.models import (
    Function,
    ScheduledTask,
    Task,
    TaskLog,
    TaskResult,
    UserFile,
    Workflow,
    WorkflowRunStep,
)
from core.utils.messaging import get_route, send_message
from core.utils.parameter import PARAMETER_TYPE

logger = get_task_logger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


class FailedTaskHandler(CeleryTask):
    """Simple wrapper to make sure failed tasks don't stay in progress"""

    def on_failure(self, exc, celery_task_id, args, kwargs, einfo):
        """Error handler.

        This is run by the worker when the task fails.

        Arguments:
            exc (Exception): The exception raised by the task.
            celery_task_id (str): Unique celery id of the failed task.
            args (Tuple): Original arguments for the task that failed.
            kwargs (Dict): Original keyword arguments for the task that failed.
            einfo (~billiard.einfo.ExceptionInfo): Exception information.

        Returns:
            None: The return value of this handler is ignored.
        """
        if (task_id := kwargs.get("task_id")) is None:
            return

        task = Task.objects.prefetch_related("tasked_object").get(id=task_id)
        mark_error(task, "Unable to send task to runner.", exc)


class InvalidStatus(Exception):
    pass


class InvalidContentObject(Exception):
    pass


def _generate_task_message(task: Task, parameters: dict) -> dict:
    """Generates tasking message from the provided Task and parameters"""
    variables = {var.name: var.value for var in task.variables}
    return {
        "id": str(task.id),
        "package": task.function.package.full_image_name,
        "function": task.function.name,
        "function_parameters": parameters,
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
    base=FailedTaskHandler,
    default_retry_delay=30,
    retry_kwargs={
        "max_retries": 3,
    },
    autoretry_for=(Exception,),
)
def publish_task(*, task_id: UUID) -> None:
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

    try:
        # This may be a retry, make sure the task is marked as IN_PROGRESS
        task.status = Task.IN_PROGRESS
        task.save()

        exchange, routing_key = get_route(task)
        send_message(
            exchange,
            routing_key,
            "TASK_PACKAGE",
            _generate_task_message(task, _handle_parameters(task)),
        )
    except Exception as exc:
        logger.info(
            f"Exception caught publishing task {task.id}, publish may be retried."
        )
        raise exc


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

    TaskLog(task=task).save_log(_protect_output(task, output))
    TaskResult(task=task).save_result(result)

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
    # This exception shouldn't occur. However, if it does, it will
    # prevent all other schedules from running.
    try:
        scheduled_task = ScheduledTask.objects.get(id=scheduled_task_id)
    except ScheduledTask.DoesNotExist:
        raise Reject(
            reason="Unable to find ScheduledTask: {0}".format(scheduled_task_id),
            requeue=False,
        )

    task = Task.objects.create(
        environment=scheduled_task.environment,
        creator=scheduled_task.creator,
        tasked_object=scheduled_task.tasked_object,
        return_type=scheduled_task.tasked_object.return_type,
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
            if task.scheduled_task is not None:
                task.scheduled_task.error()

    task.save()


def _handle_workflow_run(workflow_run_step: WorkflowRunStep, task: Task) -> None:
    """Start the next task for a WorkflowRun or update its status as appropriate"""
    workflow_task = workflow_run_step.workflow_task

    match task.status:
        case Task.COMPLETE:
            if next_step := workflow_run_step.workflow_step.next:
                try:
                    next_step.execute(workflow_task=workflow_task)
                except Exception as exc:
                    # execute handles the case where the step task is
                    # created but fails to start
                    mark_error(
                        workflow_task,
                        f"Unable to create a task for {next_step.name}",
                        error=exc,
                    )
            else:
                workflow_task.status = Task.COMPLETE
                workflow_task.save()
                # When adding workflows of workflows, here's where you
                # need to do something to continue the parent workflow
        case Task.ERROR:
            workflow_task.status = Task.ERROR
            workflow_task.save()


def _handle_parameters(task: Task) -> dict:
    """Handles processing of task parameters prior to execution.

    This function will currently mutate all file parameters into
    their corresponding presigned URLs. Since this should only be done
    before a task is sent to the runner and not be saved into the
    database, the updated parameters are returned for use.

    Args:
        task: The task that is about to be sent to the runner

    Returns:
        dict of the updated parameters
    """
    environment = task.environment
    parameters = task.parameters.copy()

    for parameter in task.tasked_object.parameters.filter(
        parameter_type=PARAMETER_TYPE.FILE, name__in=parameters.keys()
    ):
        param_name = parameter.name
        file_id = parameters[param_name]

        user_file = UserFile.objects.get(id=file_id, environment=environment)
        parameters[param_name] = user_file.file.url

    return parameters


def _start_function_task(task: Task) -> None:
    """Publishes the task for execution"""
    publish_task.delay(task_id=task.id)


def _start_workflow_task(task: Task) -> None:
    """Starts the workflow run associated with the given task"""
    from core.utils.workflow import generate_run_steps

    _ = generate_run_steps(task=task)
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
        InvalidContentObject: The tasked_object associated with the task is of an
                              unrecognized type
        InvalidStatus: The task cannot be started based on its current status
    """
    if task.status != Task.PENDING:
        raise InvalidStatus(f"Task with status f{task.status} cannot be started")

    task.status = Task.IN_PROGRESS
    task.save()

    tasked_type_class = task.tasked_type.model_class()

    if tasked_type_class not in [Function, Workflow]:
        message = f"Handling for content type {tasked_type_class} is undefined"
        mark_error(task, message, None)
        raise InvalidContentObject(message)

    try:
        if tasked_type_class is Function:
            _start_function_task(task)
        elif tasked_type_class is Workflow:
            _start_workflow_task(task)
    except Exception as exc:
        mark_error(task, "Failed to start", error=exc)


def mark_error(task, message, error=None):
    """Changes the task status to errored and logs the message"""
    task.status = Task.ERROR
    task.save()

    if message:
        extra = f" Error: {str(error)}" if error else ""
        log_message = f"{message}{extra}"
        task_log, created = TaskLog.objects.get_or_create(task=task)

        if not created:
            log_message = f"{task_log.log}\n{log_message}"

        task_log.save_log(log_message)

    if workflow_run_step := getattr(task, "workflow_run_step", None):
        mark_error(
            workflow_run_step.workflow_task,
            f"Error in step {workflow_run_step.step_name}.",
        )
