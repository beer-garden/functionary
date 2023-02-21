import django_filters
import django_tables2 as tables
from django.urls import reverse

from ui.tables.meta import BaseMeta


class TeamFilter(django_filters.FilterSet):
    team = django_filters.AllValuesFilter(field_name="name", label="Name")


class TeamTable(tables.Table):
    team = tables.Column(
        accessor="name",
        linkify=lambda record: reverse("ui:team-detail", kwargs={"pk": record.id}),
        attrs={"a": {"class": "text-decoration-none"}},
    )

    class Meta(BaseMeta):
        pass
