import django_tables2 as tables
from django.urls import reverse

from builder.models import Build


class BuildTable(tables.Table):
    package__name = tables.Column(
        linkify=lambda record: reverse("ui:build-detail", kwargs={"pk": record.id}),
    )
    created_at = tables.DateTimeColumn(
        format="N j, Y, g:i a",
    )

    class Meta:
        model = Build
        fields = ("package__name", "status", "created_at", "creator")
        attrs = {"class": "table is-striped is-hoverable is-fullwidth"}
