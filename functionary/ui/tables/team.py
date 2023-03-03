import django_filters
import django_tables2 as tables
from django.urls import reverse

from ui.tables.meta import BaseMeta


class TeamFilter(django_filters.FilterSet):
    team = django_filters.AllValuesFilter(field_name="name", label="Team")


class TeamTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:team-detail", kwargs={"pk": record.id}),
        attrs={"a": {"class": "text-decoration-none"}},
        verbose_name="Team",
    )

    class Meta(BaseMeta):
        pass
