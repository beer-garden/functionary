import itertools
import json
import logging

from celery import Task

import docker

from .celery import app
from .message_queue import send_message

OUTPUT_SEPARATOR = b"==== Output From Command ====\n"

logger = logging.getLogger(__name__)


class PackageClient(Task):
    def __init__(self):
        self._docker = docker.from_env()


@app.task(
    base=PackageClient,
    bind=True,
    default_retry_delay=30,
    retry_kwargs={
        "max_retries": 3,
    },
    autoretry_for=(docker.errors.DockerException,),
)
def pull_image(self, task) -> None:
    package = task.get("package")
    self._docker.images.pull(package)

    logger.debug(f"Pulled {package}")


@app.task(base=PackageClient, bind=True)
def run_task(self, _=None, task=None):
    exit_status, output, result = _run_task(self, task)

    return {
        "functionary_id": task["id"],
        "status": exit_status,
        "output": output.decode(),
        "result": result.decode(),
    }


def _run_task(client, task):
    package = task.get("package")
    function = task.get("function")
    parameters = json.dumps(task["function_parameters"])
    run_command = ["--function", function, "--parameters", parameters]

    logging.debug("Running %s from package %s", function, package)
    container = client._docker.containers.run(
        package, auto_remove=False, detach=True, command=run_command
    )

    exit_status = container.wait()["StatusCode"]
    output, result = _parse_container_logs(container.logs(stream=True))

    container.remove()

    return (exit_status, output, result)


def _parse_container_logs(logs):
    output = b"".join(itertools.takewhile(lambda x: x != OUTPUT_SEPARATOR, logs))
    result = b"".join(logs)

    return output, result


@app.task(
    base=PackageClient,
    bind=True,
    default_retry_delay=30,
    retry_kwargs={
        "max_retries": 3,
    },
    autoretry_for=(Exception,),
)
def publish_result(self, result):
    # TODO: The routing key should come from the configuration information received
    #       during runner registration.
    send_message("tasking.results", "TASK_RESULT", result)
