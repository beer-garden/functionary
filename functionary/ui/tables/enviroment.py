import django_filters
import django_tables2 as tables
from django.urls import reverse

from ui.tables.meta import BaseMeta


class EnviromentFilter(django_filters.FilterSet):
    environment = django_filters.AllValuesFilter(field_name="name", label="Environment")
    team = django_filters.AllValuesFilter(field_name="team__name", label="Team")


class EnvironmentTable(tables.Table):
    environment = tables.Column(
        accessor="name",
        linkify=lambda record: reverse(
            "ui:environment-detail", kwargs={"pk": record.id}
        ),
        attrs={"a": {"class": "text-decoration-none"}},
        verbose_name="Environment",
    )
    team = tables.Column(
        accessor="team__name",
        linkify=lambda record: reverse("ui:team-detail", kwargs={"pk": record.team.id}),
        attrs={"a": {"class": "text-decoration-none"}},
        verbose_name="Team",
    )

    class Meta(BaseMeta):
        pass
