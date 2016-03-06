from django.db import models
from django.dispatch import receiver

from boardinghouse.base import SharedSchemaMixin


class TemplateSchema(SharedSchemaMixin, models.Model):
    """
    A ``boardinghouse.contrib.template.models.TemplateSchema`` can be used
    for creating a new schema complete with some initial data.
    """
    template_schema_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        default_permissions = ('add', 'change', 'delete', 'view', 'activate', 'clone')
        verbose_name_plural = u'template schemata'

    def __unicode__(self):
        return self.name

    @property
    def schema(self):
        return '__template_{}'.format(self.pk)

    @classmethod
    def create_from_schema(cls, schema='__template__'):
        pass

    def clone_to_schema(self, schema):
        pass
