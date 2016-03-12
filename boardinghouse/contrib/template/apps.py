from django.apps import AppConfig
from django.db import models
from django.dispatch import receiver

from boardinghouse.schema import activate_schema


class BoardingHouseTemplateConfig(AppConfig):
    name = 'boardinghouse.contrib.template'

    def ready(self):
        from boardinghouse import signals
        from .models import SchemaTemplate

        models.signals.post_save.connect(signals.create_schema,
                                         sender=SchemaTemplate,
                                         dispatch_uid='create-schema-template')

        models.signals.post_delete.connect(signals.drop_schema, sender=SchemaTemplate)

        @receiver(signals.schema_aware_operation, weak=False)
        def execute_on_all_templates(sender, db_table, function, **kwargs):
            for schema in SchemaTemplate.objects.all():
                activate_schema(schema.schema)
                function(*kwargs.get('args', []), **kwargs.get('kwargs', {}))
