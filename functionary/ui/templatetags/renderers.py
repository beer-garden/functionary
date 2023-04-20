import django_tables2 as tables
from django import template
from django.template.loader import get_template, select_template
from django_tables2.templatetags.django_tables2 import RenderTableNode

register = template.Library()


class RenderTableNodeInContext(RenderTableNode):
    """Render the table from a template.

    The django_tables2 Table Renderer causes an additional context to be created which
    also results in all the context processors running again. This class avoids the
    extra context creation.
    """

    def render(self, context):
        """Render the table node using the given context.

        Args:
            context: the context to render with
        """
        table = self.table.resolve(context)

        request = context.get("request")

        if isinstance(table, tables.Table):
            pass
        elif hasattr(table, "model"):
            queryset = table

            table = tables.table_factory(model=queryset.model)(
                queryset, request=request
            )
        else:
            raise ValueError(f"Expected table or queryset, not {type(table).__name__}")

        if self.template_name:
            template_name = self.template_name.resolve(context)
        else:
            template_name = table.template_name

        if isinstance(template_name, str):
            template = get_template(template_name)
        else:
            # assume some iterable was given
            template = select_template(template_name)

        try:
            # Different HACK from django_tables2:
            # TemplateColumn benefits from being able to use the context
            # that the table is rendered in. The current way this is
            # achieved is to temporarily attach the context to the table,
            # which TemplateColumn then looks for and uses.
            table.context = context
            context.update({"table": table})
            table.before_render(request)

            # This template dereference is to prevent the template from creating
            # a brand new context for the table render. Normally a new context is
            # created when rendering a template, but we want to use the context that
            # we already have instead.
            # If this were to create a new context, all the ContextProcessors would run
            # again and that's a bad thing.
            return template.template.render(context)
        finally:
            # remove the table we added to the context
            context.pop()
            del table.context


@register.tag
def render_table(parser, token):
    """Render a HTML table.

    This tag is a copy of the django_tables2 render_table tag. The tag can be given
    either a Table object, or a queryset. An optional second argument can specify the
    template to use.

    Example:
        {% render_table table %}
        {% render_table table "custom.html" %}
        {% render_table user_queryset %}
    """
    bits = token.split_contents()
    bits.pop(0)

    table = parser.compile_filter(bits.pop(0))
    template = parser.compile_filter(bits.pop(0)) if bits else None

    return RenderTableNodeInContext(table, template)
