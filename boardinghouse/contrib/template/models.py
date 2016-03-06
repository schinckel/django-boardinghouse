from django.db import models
from django.dispatch import receiver

from boardinghouse.base import SharedSchemaMixin


class TemplateSchema(SharedSchemaMixin, models.Model):
    """
    A ``boardinghouse.contrib.template.models.TemplateSchema``
    """
    name = models.CharField(max_length=128, unique=True)

    class Meta:
        default_permissions = ('add', 'change', 'delete', 'view', 'activate')
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


@receiver(models.signals.post_save, sender=TemplateSchema)
def create_template_schema(sender, instance, **kwargs):
    assert None, "Create schema missing."
