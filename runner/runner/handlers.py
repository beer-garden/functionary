import itertools
import json
import logging
from os import getenv

import docker
from celery import Task
from docker.errors import APIError, DockerException

from .celery import app
from .messaging import send_message
from .utils import create_failed_result, create_result

OUTPUT_SEPARATOR = b"==== Output From Command ====\n"

logger = logging.getLogger(__name__)


class ResultPublishingTask(Task):
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
        if (task := kwargs.get("task")) is None:
            return

        result = create_failed_result(task, f"Task execution failed: {exc}")
        publish_result.delay(result)


class DockerClientError(Exception):
    pass


def _login_docker_client(client: docker.DockerClient):
    """Login the given DockerClient.

    Args:
        client: The DockerClient to login
    """
    username = getenv("REGISTRY_USER")
    password = getenv("REGISTRY_PASSWORD")
    registry = getenv("REGISTRY_HOST")

    if port := getenv("REGISTRY_PORT"):
        registry += f":{port}"

    if username and password:
        try:
            client.login(username=username, password=password, registry=registry)
        except APIError as exc:
            logger.critical("Docker login failed. Check REGISTRY_* settings.")
            raise DockerClientError(f"Docker login failed: {exc}")


def _get_docker_client(login: bool = False) -> docker.DockerClient:
    """Configures a DockerClient and optionally logs in.

    Args:
        login: True to also login the DockerClient
    Raises:
        DockerClientError: Setup of the docker client failed
    """
    try:
        client = docker.from_env()
    except DockerException as exc:
        logger.critical("Unable to establish docker socket connection.")
        raise DockerClientError(f"Docker client setup failed: {exc}")

    if login:
        _login_docker_client(client)

    return client


@app.task(
    default_retry_delay=30,
    retry_kwargs={
        "max_retries": 3,
    },
    autoretry_for=(DockerException,),
)
def pull_image(*, package) -> None:
    package = package.get("image_name")

    docker_client = _get_docker_client(login=True)
    try:
        docker_client.images.pull(package)
    except DockerException as exc:
        logger.warning(f"Unable to pull docker image for {package}.")
        raise DockerClientError(f"Docker image pull failed: {exc}")

    logger.debug(f"Pulled {package}")


@app.task(base=ResultPublishingTask)
def run_task(*, task):
    task_id = task.get("id")
    package = task.get("package")
    function = task.get("function")
    parameters = json.dumps(task["function_parameters"])
    variables = task.get("variables")
    run_command = ["--function", function, "--parameters", parameters]

    logger.info(
        "Task %s running (function: %s, package %s)", task_id, function, package
    )
    docker_client = _get_docker_client()
    try:
        kwargs = {
            "auto_remove": False,
            "detach": True,
            "command": run_command,
            "environment": variables,
        }

        if network := getenv("FUNCTIONARY_NETWORK"):
            kwargs["network"] = network
        elif network_mode := getenv("FUNCTIONARY_NETWORK_MODE"):
            kwargs["network_mode"] = network_mode

        try:
            # Run the container assuming the image has been pulled.
            container = docker_client.containers.run(package, **kwargs)
        except APIError:
            # The run function should result in an APIError if the image doesn't
            # exist and it's not able to be pulled. Login and try again.
            logger.debug("Failed to run container, authenticating and retrying")

            _login_docker_client(docker_client)
            docker_client.images.pull(package)
            container = docker_client.containers.run(package, **kwargs)
    except DockerException as exc:
        raise Exception(f"Unable to execute function. Encountered error: {exc}")

    try:
        exit_status = container.wait()["StatusCode"]
        logs = container.logs(stream=True)
        output = b"".join(
            itertools.takewhile(lambda x: x != OUTPUT_SEPARATOR, logs)
        ).rstrip()
        result = b"".join(logs).rstrip()
        logger.info("Task %s succeeded", task_id)
    except Exception as exc:  # raises both APIError and requests.exceptions.ReadTimeout
        raise Exception(f"Unable to get result. Encountered error: {exc}")

    try:
        container.remove()
    except DockerException:
        # Failing cleanup shouldn't fail the whole task, log a message
        logger.info(f"Unable to remove container for task {task['id']}")

    return create_result(task, exit_status, output, result)


@app.task(
    default_retry_delay=30,
    retry_kwargs={
        "max_retries": 3,
    },
    autoretry_for=(Exception,),
)
def publish_result(result):
    # TODO: The routing key should come from the configuration information received
    #       during runner registration.
    send_message("tasking.results", "TASK_RESULT", result)
    logger.info("Task %s result published", result["task_id"])
