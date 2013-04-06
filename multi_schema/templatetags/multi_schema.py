from django import template

from ..models import Schema

register = template.Library()

@register.filter
def is_schema_aware(obj):
    return obj and obj._is_schema_aware

@register.filter
def schema_name(pk):
    if not pk:
        return "no schema"
    return Schema.objects.get(pk=pk).name