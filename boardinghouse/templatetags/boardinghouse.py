from django import template

from ..models import Schema
from ..schema import is_shared_model

register = template.Library()

@register.filter
def is_schema_aware(obj):
    return not is_shared_model(obj)

register.filter(is_shared_model)

@register.filter
def schema_name(pk):
    try:
        return Schema.objects.get(pk=pk).name
    except Schema.DoesNotExist:
        return "no schema"
