from django import template

from ..schema import is_shared_model as _is_shared_model
from ..signals import find_schema

register = template.Library()


@register.filter
def is_schema_aware(obj):
    return obj and not _is_shared_model(obj)


@register.filter
def is_shared_model(obj):
    return obj and _is_shared_model(obj)


@register.filter
def schema_name(schema):
    for handler, response in find_schema.send(sender=None, schema=schema):
        if response:
            return response.name
    return 'no schema'
