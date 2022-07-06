""" Schedule model """
from django.db import models


class Schedule(models.Model):
    """
    ScheduleTask is a task scheduled to run at some future point or interval

    Attributes:
        name: the name of schedule task
    """

    name = models.CharField(max_length=64, unique=True, db_index=True)

    def __str__(self):
        return self.name
