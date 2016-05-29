"""
Signals that are fired as part of the django-boardinghouse project.

.. data:: schema_created

    Sent when a new schema object has been created in the database. Accepts a
    single argument, the (internal) name of the schema.

.. data:: schema_pre_activate

    Sent just before a schema will be activated. May be used to abort this by
    throwing an exception.

.. data:: schema_post_activate

    Sent immediately after a schema has been activated.

.. data:: session_requesting_schema_change

    Sent when a user-session has requested (and is, according to default rules,
    allowed to change to this schema). May be used to prevent the change, by
    throwing an exception.

.. data:: session_schema_changed

    Sent when a user-session has changed it's schema.

.. data:: schema_aware_operation

    Sent when a migration operation that needs to be applied to each schema is
    due to be applied. Internally, this signal is used to ensure that the
    template schema and all currently existing schemata have the migration
    applied to them.

    This is also used by the ``contrib.template`` app to ensure that operations
    are applied to :class:`boardinghouse.contrib.template.models.SchemaTemplate`
    instances.

"""

from django.dispatch import Signal

schema_created = Signal(providing_args=["schema"])
schemata_deleted = Signal(providing_args=["schemata"])

schema_pre_activate = Signal(providing_args=["schema"])
schema_post_activate = Signal(providing_args=["schema"])

session_requesting_schema_change = Signal(providing_args=["user", "schema", "session"])
session_schema_changed = Signal(providing_args=["user", "schema", "session"])

schema_aware_operation = Signal(providing_args=['db_table', 'sql', 'params', 'execute'])
