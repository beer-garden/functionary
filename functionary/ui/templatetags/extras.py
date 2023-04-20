import json

from django import template
from django.conf import settings

register = template.Library()


@register.filter
def applied_filters(filter_data):
    filter_data = filter_data or {}
    return [field for field, value in filter_data.items() if value]


@register.filter
def pretty_json(value):
    return json.dumps(value, indent=4)


@register.simple_tag
def documentation_link():
    return settings.DOCUMENTATION_LINK
