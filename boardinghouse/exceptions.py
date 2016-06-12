class Forbidden(Exception):
    """
    An exception that will be raised when an attempt to activate a non-valid
    schema is made.
    """


class TemplateSchemaActivation(Forbidden):
    """
    An exception that will be raised when a user attempts to activate
    the settings.TEMPLATE_SCHEMA schema.
    """
    def __init__(self, *args, **kwargs):
        super(TemplateSchemaActivation, self).__init__(
            'Activating template schema forbidden.', *args, **kwargs
        )


class SchemaNotFound(Exception):
    """
    An exception that is raised when an attempt to activate a schema that
    is not in the database is made.
    """


class SchemaRequiredException(Exception):
    """
    An exception raised when an operation requires a schema to be active
    or supplied, but none was provided.
    """
