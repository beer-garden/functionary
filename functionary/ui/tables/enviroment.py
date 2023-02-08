import django_tables2 as tables
from django.urls import reverse


class EnvironmentTable(tables.Table):
    environment = tables.Column(
        accessor="name",
        linkify=lambda record: reverse(
            "ui:environment-detail", kwargs={"pk": record.id}
        ),
    )
    team = tables.Column(
        accessor="team__name",
        linkify=lambda record: reverse("ui:team-detail", kwargs={"pk": record.team.id}),
    )

    class Meta:
        attrs = {"class": "table is-striped is-hoverable is-fullwidth"}
