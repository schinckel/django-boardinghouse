from django.db import models

class SchemaAwareModel(models.Model):
    """
    The Base class for models that should be in a seperate schema.
    
    You could just put `_is_schema_aware` on your model class, though.
    """
    _is_schema_aware = True

    class Meta:
        abstract = True
