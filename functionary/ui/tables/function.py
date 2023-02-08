import django_tables2 as tables
from django.urls import reverse

from core.models import Function


class FunctionTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:function-detail", kwargs={"pk": record.id}),
    )
    package = tables.Column(
        linkify=lambda record: reverse(
            "ui:package-detail", kwargs={"pk": record.package.id}
        ),
    )

    class Meta:
        model = Function
        fields = ("name", "package", "summary")
        attrs = {"class": "table is-striped is-hoverable is-fullwidth"}
