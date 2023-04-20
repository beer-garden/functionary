import django_filters
import django_tables2 as tables
from django.utils.html import format_html

from core.models import UserFile
from ui.tables import DATETIME_FORMAT
from ui.tables.meta import BaseMeta

BOOLEAN_CHOICES = (
    (True, "Yes"),
    (False, "No"),
)


class UserFileFilter(django_filters.FilterSet):
    name = django_filters.Filter(label="Name", lookup_expr="startswith")
    public = django_filters.ChoiceFilter(
        label="Public", choices=BOOLEAN_CHOICES, empty_label=""
    )

    class Meta:
        model = UserFile
        fields = ["name", "public"]


class UserFileTable(tables.Table):
    created_at = tables.DateTimeColumn(format=DATETIME_FORMAT, verbose_name="Created")
    menu_button = tables.TemplateColumn(
        orderable=False,
        verbose_name="",
        template_name="partials/userfile/table_menu.html",
    )

    class Meta(BaseMeta):
        model = UserFile
        fields = ("name", "public", "created_at")
        orderable = True
        empty_text = "No files found"


class SelectableUserFileTable(tables.Table):
    selected_id = tables.Column(
        accessor="id",
        verbose_name="Select",
        orderable=False,
    )
    created_at = tables.DateTimeColumn(format=DATETIME_FORMAT, verbose_name="Created")

    class Meta(BaseMeta):
        model = UserFile
        fields = ["selected_id", "name", "public", "created_at"]
        order_by = ("name",)
        empty_text = "No files found"

    def render_selected_id(self, value):
        return format_html(
            "<input type='radio' id='{value}' name='selected_file' value='{value}' />",
            value=value,
        )


class SelectableCreatorUserFileTable(SelectableUserFileTable):
    class Meta(SelectableUserFileTable.Meta):
        fields = ["selected_id", "name", "created_at", "creator"]
        exclude = ["public"]
