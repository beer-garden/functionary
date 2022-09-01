import logging
from uuid import UUID

from celery.utils.log import get_task_logger
from django.conf import settings

from core.celery import app
from core.models import Task
from core.utils.messaging import get_route, send_message

logger = get_task_logger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


def _generate_task_message(task: Task) -> dict:
    """Generates tasking message from the provided Task"""
    return {
        "id": str(task.id),
        "package": task.function.package.full_image_name,
        "function": task.function.name,
        "function_parameters": task.parameters,
    }


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

    task = Task.objects.select_related("function", "function__package").get(id=task_id)

    exchange, routing_key = get_route(task)
    send_message(exchange, routing_key, "TASK_PACKAGE", _generate_task_message(task))
