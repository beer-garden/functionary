import django_tables2 as tables
from django.utils.html import format_html

from ui.tables.meta import BaseMeta
from ui.templatetags.social_helper import find_account


class AccountConnectionsTable(tables.Table):
    provider = tables.Column(accessor="name")
    account = tables.Column(accessor="provider")
    action_buttons = tables.TemplateColumn(
        verbose_name="",
        template_name="partials/socialaccount/actions.html",
    )

    class Meta(BaseMeta):
        empty_text = "No accounts defined"

    def render_provider(self, value, record):
        return format_html(
            f'<span class="icon-{record["provider"].id}"> {value}</span>'
        )

    def render_account(self, value):
        account = find_account(self.context, value.id)
        return f"{account['username']}" if account else ""
