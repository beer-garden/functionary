import json as json_

from django import template
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()


@register.filter
def json_safe(value):
    """Template filter to convert values to a form that's safe for use in JSON"""
    return (
        value.replace('"', '\\"')
        if isinstance(value, str)
        else json_.dumps(value, cls=DjangoJSONEncoder)
    )
