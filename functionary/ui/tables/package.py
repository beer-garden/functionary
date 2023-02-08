import django_tables2 as tables
from django.urls import reverse

from core.models import Package


class PackageTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:package-detail", kwargs={"pk": record.id}),
    )

    class Meta:
        model = Package
        fields = ("name", "summary")
        attrs = {"class": "table is-striped is-hoverable is-fullwidth"}
