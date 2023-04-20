def create_result(
    task: dict, status: int, output: str | bytes, result: str | bytes
) -> dict:
    """Creates a task result.

    Args:
        task: the task dict parameter that was passed to the celery task
        status: integer status code for the result
        output: task output log
        result: task result

    Returns:
        Task result as a dict in the correct format for the result message
    """
    return {
        "task_id": task["id"],
        "status": status,
        "output": output.decode() if isinstance(output, bytes) else output,
        "result": result.decode() if isinstance(result, bytes) else result,
    }


def create_failed_result(task: dict, log: str):
    """Helper method to create a failed task result indicated by a status of 1.

    Args:
        task: the task dict parameter that was passed to the celery task
        log: the output log

    Returns:
        Task result as a dict in the correct format for the result message
    """
    return create_result(task, 1, log, "")
