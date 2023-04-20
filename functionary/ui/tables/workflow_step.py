import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

from ui.tables.meta import BaseMeta


class WorflowStepTable(tables.Table):
    start_actions = tables.TemplateColumn(
        verbose_name="",
        template_name="partials/workflows/step_start_actions.html",
    )
    name = tables.Column()
    task = tables.Column(accessor="tasked_object__display_name")
    parameters = tables.Column(accessor="parameter_template")
    end_action_buttons = tables.TemplateColumn(
        verbose_name="",
        template_name="partials/workflows/step_end_actions.html",
    )

    class Meta(BaseMeta):
        empty_text = "No steps defined"
        row_attrs = {"class": "grab align-middle text-nowrap"}

    def __init__(self, data, workflow_pk, *args, **kwargs):
        attrs = kwargs.pop("attrs", {})
        if "tbody" not in attrs:
            attrs["tbody"] = {
                "class": "sortable",
                "hx-post": reverse(
                    "ui:workflowsteps-reorder",
                    kwargs={"workflow_pk": workflow_pk},
                ),
                "hx-trigger": "end",
                "hx-target": "#workflow-steps",
                "hx-swap": "outerHTML",
            }
        if "class" not in attrs:
            attrs["class"] = "table table-striped table-hover"
        super().__init__(
            data=data,
            attrs=attrs,
            *args,
            **kwargs,
        )

    def render_task(self, value, record):
        if record.tasked_type.name == "function":
            icon_class = "fa-cube"
        else:
            icon_class = "fa-diagram-next"
        return format_html(f"<i class='fa {icon_class}'></i> {value}")
