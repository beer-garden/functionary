import django_tables2 as tables
from django.urls import reverse

from ui.tables import DATETIME_FORMAT
from ui.tables.meta import BaseMeta


class ScheduledTaskHistory(tables.Table):
    created_at = tables.DateTimeColumn(
        format=DATETIME_FORMAT,
        verbose_name="Ran at",
        linkify=lambda record: reverse("ui:task-detail", kwargs={"pk": record.id}),
    )
    status = tables.Column()

    class Meta(BaseMeta):
        empty_text = "No recent history"
