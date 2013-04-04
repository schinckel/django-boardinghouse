from django.db import models

class SchemaAware(object):
    _is_schema_aware = True

class SchemaAwareModel(SchemaAware, models.Model):
    """
    The Base class for models that should be in a seperate schema.
    
    You could just put `_is_schema_aware = True` on your model class, though.
    """

    class Meta:
        abstract = True
