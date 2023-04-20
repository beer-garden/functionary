from django import template
from django.urls import reverse

register = template.Library()

NAV_ITEMS = [
    {
        "label": "Tasking",
        "icon": "fa-clipboard-list",
        "active": "task",
        "link": reverse("ui:task-list"),
    },
    {
        "label": "Schedules",
        "icon": "fa-clock",
        "active": "scheduledtask",
        "link": reverse("ui:scheduledtask-list"),
    },
    {
        "label": "Workflows",
        "icon": "fa-diagram-next",
        "active": "workflow",
        "link": reverse("ui:workflow-list"),
    },
    {
        "label": "Functions",
        "icon": "fa-cube",
        "active": "function",
        "link": reverse("ui:function-list"),
    },
    {
        "label": "Packages",
        "icon": "fa-cubes",
        "active": "package",
        "link": reverse("ui:package-list"),
    },
    {
        "label": "Builds",
        "icon": "fa-wrench",
        "active": "build",
        "link": reverse("ui:build-list"),
    },
    {
        "label": "Files",
        "icon": "fa-file",
        "active": "file",
        "link": reverse("ui:file-list"),
    },
]


@register.inclusion_tag("partials/nav_pills.html", takes_context=True)
def nav_pills(context):
    return {"nav_list": NAV_ITEMS, "active_nav": context["active_nav"]}
