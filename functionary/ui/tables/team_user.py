import django_tables2 as tables
from django.utils.html import format_html

from ui.tables.meta import BaseMeta


class TeamUserTable(tables.Table):
    name = tables.Column(accessor="user")
    username = tables.Column(accessor="user__username")
    role = tables.Column()
    action_buttons = tables.TemplateColumn(
        verbose_name="",
        template_name="partials/teams/table_actions.html",
    )

    class Meta(BaseMeta):
        empty_text = "No users defined"

    def render_name(self, value):
        return format_html(f"{value.first_name} {value.last_name}")
