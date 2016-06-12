import sys

from django.conf import settings
from django.db import models
from django.utils import six
from django.utils.functional import lazy

from boardinghouse.base import SharedSchemaMixin
from boardinghouse.schema import (
    activate_schema, deactivate_schema, get_schema_model,
)


def verbose_name_plural():
    if 'makemigrations' in sys.argv:
        return u'template schemata'
    return u'template {0}'.format(get_schema_model()._meta.verbose_name_plural)


def verbose_name():
    if 'makemigrations' in sys.argv:
        return u'template schema'
    return u'template {0}'.format(get_schema_model()._meta.verbose_name)


class SchemaTemplateQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(is_active=True)


@six.python_2_unicode_compatible
class SchemaTemplate(SharedSchemaMixin, models.Model):
    """
    A ``boardinghouse.contrib.template.models.SchemaTemplate`` can be used
    for creating a new schema complete with some initial data.
    """
    template_schema_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)

    objects = SchemaTemplateQuerySet.as_manager()

    class Meta:
        default_permissions = ('add', 'change', 'delete', 'view', 'activate', 'clone')
        verbose_name = lazy(verbose_name, six.text_type)()
        verbose_name_plural = lazy(verbose_name_plural, six.text_type)()

    def __str__(self):
        return self.name

    @property
    def schema(self):
        return '{0}{1}'.format(settings.BOARDINGHOUSE_TEMPLATE_PREFIX, self.pk)

    def activate(self):
        activate_schema(self.schema)

    def deactivate(self):
        deactivate_schema()
