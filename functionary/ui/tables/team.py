import django_tables2 as tables
from django.urls import reverse


class TeamTable(tables.Table):
    team = tables.Column(
        accessor="name",
        linkify=lambda record: reverse("ui:team-detail", kwargs={"pk": record.id}),
    )

    class Meta:
        attrs = {"class": "table is-striped is-hoverable is-fullwidth"}
