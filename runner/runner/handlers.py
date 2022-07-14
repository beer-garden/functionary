import itertools
import json
import logging
import os

from celery import Task

import docker

from .celery import app
from .message_queue import send_message

OUTPUT_SEPARATOR = b"==== Output From Command ====\n"

logger = logging.getLogger(__name__)


class PackageClient(Task):
    REGISTRY = os.environ.get("REGISTRY", "localhost:5000")

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
    fqi = f"{self.REGISTRY}/{package}"
    self._docker.images.pull(fqi)

    logger.debug(f"Pulled {fqi}")
    return task


@app.task(base=PackageClient, bind=True)
def run_task(self, task):
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
def publish_result(self, result, topic):
    send_message(topic, "TASK_RESULT", result)
