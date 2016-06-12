from django.conf import settings
from django.db import models
from django.dispatch import receiver

from boardinghouse.schema import _table_exists
from boardinghouse import signals
from boardinghouse.receivers import create_schema, drop_schema

from .models import DemoSchema

models.signals.post_save.connect(create_schema,
                                 sender=DemoSchema,
                                 dispatch_uid='create-demo-schema')

models.signals.post_delete.connect(drop_schema, sender=DemoSchema)


@receiver(signals.schema_aware_operation, weak=False, dispatch_uid='execute-all-demo-schemata')
def execute_on_all_templates(sender, db_table, function, **kwargs):
    if _table_exists(DemoSchema._meta.db_table):
        for schema in DemoSchema.objects.active():
            schema.activate()
            function(*kwargs.get('args', []), **kwargs.get('kwargs', {}))


@receiver(signals.session_requesting_schema_change, weak=False, dispatch_uid='change-to-demo-schema')
def change_to_demo_schema(sender, schema, user, session, **kwargs):
    if schema == '{0}{1}'.format(settings.BOARDINGHOUSE_DEMO_PREFIX, user.pk):
        return user.demo_schema


@receiver(signals.find_schema, weak=False, dispatch_uid='search-for-demo-schema')
def find_demo_schema(sender, schema, **kwargs):
    if schema and schema.startswith(settings.BOARDINGHOUSE_DEMO_PREFIX):
        return DemoSchema.objects.get(user=schema.split(settings.BOARDINGHOUSE_DEMO_PREFIX)[1])
