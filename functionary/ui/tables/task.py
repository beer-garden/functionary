import django_tables2 as tables
from django.urls import reverse

from core.models import Task


class TaskListTable(tables.Table):
    function = tables.Column(
        linkify=lambda record: reverse("ui:task-detail", kwargs={"pk": record.id}),
    )

    created_at = tables.DateTimeColumn(
        format="N j, Y, g:i a",
    )

    class Meta:
        model = Task
        fields = ("function", "status", "creator", "created_at")
        attrs = {"class": "table is-striped is-hoverable is-fullwidth"}
