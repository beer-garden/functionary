import django_tables2 as tables
from django.utils.html import format_html

from ui.tables.meta import BaseMeta


class WorflowParameterTable(tables.Table):
    name = tables.Column()
    description = tables.Column()
    type = tables.Column(accessor="parameter_type", verbose_name="Type")
    required = tables.Column()
    action_buttons = tables.TemplateColumn(
        verbose_name="",
        template_name="partials/workflows/parameter_actions.html",
    )

    class Meta(BaseMeta):
        empty_text = "No parameters defined"

    def render_required(self, value):
        if value:
            return format_html("<i class='fa fa-check' />")
        else:
            return ""
