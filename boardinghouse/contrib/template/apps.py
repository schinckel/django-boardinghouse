from django.apps import AppConfig
from django.db import models


class BoardingHouseTemplateConfig(AppConfig):
    name = 'boardinghouse.contrib.template'

    def ready(self):
        from boardinghouse import signals
        from .models import SchemaTemplate

        models.signals.post_save.connect(signals.create_schema,
                                         sender=SchemaTemplate,
                                         dispatch_uid='create-schema-template')

        models.signals.post_delete.connect(signals.drop_schema, sender=SchemaTemplate)
