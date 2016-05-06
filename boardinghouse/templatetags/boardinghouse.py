from django import template

from ..schema import _get_schema, is_shared_model as _is_shared_model

register = template.Library()


@register.filter
def is_schema_aware(obj):
    return obj and not _is_shared_model(obj)


@register.filter
def is_shared_model(obj):
    return obj and _is_shared_model(obj)


@register.filter
def schema_name(schema):
    try:
        return _get_schema(schema).name
    except AttributeError:
        return "no schema"
