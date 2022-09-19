from django.db import models


class TaskLog(models.Model):
    """Log output from the execution of a Task"""

    task = models.OneToOneField(primary_key=True, to="Task", on_delete=models.CASCADE)
    log = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
