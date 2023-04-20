import django_tables2 as tables
from django.utils.html import format_html

from ui.tables.meta import BaseMeta


class VariableTable(tables.Table):
    name = tables.Column()
    value = tables.Column()
    action_buttons = tables.TemplateColumn(
        verbose_name="",
        template_name="partials/variable_actions.html",
    )

    class Meta(BaseMeta):
        empty_text = "None"

    def render_value(self, value, record):
        if record.protect:
            value = "<span title='Protected Value'>•••••</span>"
        return format_html(value)
