from django.conf import settings
from django.dispatch import receiver
from django.db import models

from boardinghouse import signals
from boardinghouse.exceptions import Forbidden
from boardinghouse.receivers import create_schema, drop_schema
from boardinghouse.schema import _table_exists

from .models import SchemaTemplate

models.signals.post_save.connect(create_schema,
                                 sender=SchemaTemplate,
                                 dispatch_uid='create-schema-template')

models.signals.post_delete.connect(drop_schema, sender=SchemaTemplate)


@receiver(signals.schema_aware_operation, weak=False, dispatch_uid='execute-all-templates')
def execute_on_all_templates(sender, db_table, function, **kwargs):
    if _table_exists(SchemaTemplate._meta.db_table):
        for schema in SchemaTemplate.objects.all():
            schema.activate()
            function(*kwargs.get('args', []), **kwargs.get('kwargs', {}))


@receiver(signals.session_requesting_schema_change, weak=False, dispatch_uid='change-to-schema-template')
def change_to_schema_template(sender, schema, user, session, **kwargs):
    if schema.startswith(settings.BOARDINGHOUSE_TEMPLATE_PREFIX):
        if not user.is_superuser and not user.is_staff:
            raise Forbidden()

        try:
            return SchemaTemplate.objects.get(pk=schema.split(settings.BOARDINGHOUSE_TEMPLATE_PREFIX)[1])
        except SchemaTemplate.DoesNotExist:
            raise Forbidden()


@receiver(signals.find_schema, weak=False, dispatch_uid='find-schema-template')
def find_schema_template(sender, schema, **kwargs):
    if schema and schema.startswith(settings.BOARDINGHOUSE_TEMPLATE_PREFIX):
        return SchemaTemplate.objects.get(pk=schema.split(settings.BOARDINGHOUSE_TEMPLATE_PREFIX)[1])
