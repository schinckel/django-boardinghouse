from django.apps import AppConfig
from django.db import models
from django.dispatch import receiver


class BoardingHouseDemoConfig(AppConfig):
    name = 'boardinghouse.contrib.demo'

    def ready(self):
        from boardinghouse import signals
        from .models import DemoSchema

        models.signals.post_save.connect(signals.create_schema,
                                         sender=DemoSchema,
                                         dispatch_uid='create-demo-schema')

        models.signals.post_delete.connect(signals.drop_schema, sender=DemoSchema)

        @receiver(signals.schema_aware_operation, weak=False, dispatch_uid='execute-all-demo-schemata')
        def execute_on_all_templates(sender, db_table, function, **kwargs):
            DemoSchema.objects.expired().delete()

            for schema in DemoSchema.objects.active():
                schema.activate()
                function(*kwargs.get('args', []), **kwargs.get('kwargs', {}))
