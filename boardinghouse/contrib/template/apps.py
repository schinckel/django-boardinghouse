from django.apps import AppConfig
from django.db import models, connection


class BoardingHouseTemplateConfig(AppConfig):
    name = 'boardinghouse.contrib.template'

    def ready(self):
        from boardinghouse import signals
        from .models import TemplateSchema

        models.signals.post_save.connect(signals.create_schema,
                                         sender=TemplateSchema,
                                         dispatch_uid='create-template-schema')

        def delete_template_schema(sender, instance, **kwargs):
            if isinstance(instance, TemplateSchema):
                connection.cursor().execute('DROP SCHEMA {} CASCADE'.format(instance.schema))

        models.signals.post_delete.connect(delete_template_schema, sender=TemplateSchema, weak=False)
