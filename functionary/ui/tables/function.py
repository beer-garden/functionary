import django_tables2 as tables
from django.urls import reverse

from core.models import Function
from ui.tables.meta import BaseMeta


class FunctionTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:function-detail", kwargs={"pk": record.id}),
        attrs={"a": {"class": "text-decoration-none"}},
    )
    package = tables.Column(
        linkify=lambda record: reverse(
            "ui:package-detail", kwargs={"pk": record.package.id}
        ),
        attrs={"a": {"class": "text-decoration-none"}},
    )

    class Meta(BaseMeta):
        model = Function
        fields = ("name", "package", "summary")
