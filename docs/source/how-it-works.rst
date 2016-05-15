How it works (in more detail)
=============================

This is covered lightly earlier, but here is more detail about how (and why) Django Boardinghouse works as it does.


BOARDINGHOUSE_SCHEMA_MODEL
--------------------------

The core of the package revolves around a swappable model that stores all of the available schemata that a given user may switch to. When a new instance of this model is created, a new Postgres schema is cloned from the template schema.

When an instance of the model is deleted, the relevant postgres schema is dropped.

There is an abstract class you'll probably want to inherit from: :class:`boardinghouse.models.AbstractSchema`, although this is not necessary. However, there is a perfectly sane default concrete implementation: :class:`boardinghouse.models.Schema`. This contains a many-to-many field with ``settings.AUTH_USER_MODEL``, but if you need anything different, then a subclass may be your best bet.


Shared vs Private Models
------------------------

Every object in the database (table, view, index, etc) is either shared or private. A shared object means it will live in the public schema, and the data within it will be shared between all tenants. For instance, the `auth_user` table (and therefore the `auth.User` model) are shared objects. This in particular is required, because user authentication needs to occur before we can determine which tenant schema should be activated.

The rules for determining if a model (and therefore it's related database objects) should be shared or private are:

* Is the model explicitly marked as shared? This can be done by subclassing :class:`boardinghouse.base.SharedSchemaModel`.
* Is the model listed in `settings.BOARDINGHOUSE_SHARED_MODELS`?
* Is the model/table a join between two public models (and not explicitly marked as private by `settings.BOARDINGHOUSE_PRIVATE_MODELS`)

It is not permissable for a shared model to have a foreign key to a private model, but it is possible for a private model to have a foreign key to a shared model.


Middleware
----------

When a request comes in, the supplied middleware determines which schema should be activated, and activates it. This involves setting the Postgres search path to (`schema-name`, public).

The system for determining if the current request should be allowed to change to the desired schema uses an extensible signals-based approach. After some basic checks have occurred, the signal :meth:`boardinghouse.signals.session_requesting_schema_change` is sent to all receivers. If a receiver needs to indicate that this user _may_ activate this schema, then it MUST return an object with a `schema` attribute (which is the in-database schema name), or a dict with a similar key-value pair. It SHOULD also return an attribute/key of `name`, which will be used if the user-friendly name of the schema being activated.

If the receiver does not have anything to say about this user-schema pair, then it MUST return `None`.

If the receiver needs to indicate that this user may _not_ activate this schema, then it MUST raise a `Forbidden` exception. However, it is worth noting that as soon as a receiver has indicated that this change is permitted, then no more receivers will be executed.

Migrations
----------

Most of the complexity of this package lies in the handling of migrations. Every time the schema editor performs an `execute()` call, it examines the SQL it is about to execute, and attempts to determine if this is a shared or private database object.

If it is a private database object, then a signal is sent:

:meth:`boardinghouse.signals.schema_aware_operation`

The signal is sent with the database table, the (execute) function that needs to be executed, and the arguments that should be aplied to that function.

The default schema handling is then to iterate through all known schemata, and call the function with the supplied arguments, but it is possible to deregister the default handler, and implement your own logic.

It's also possible to have other listeners: for instance the same signal is handled by the template schema migration handling, and regular schema migration handling.

It is worth noting that this logic works for all django migration operations, with the exception of the `RunPython` operation. Because of the way this works, the `execute` method is not called (unless the operation itself calls it).

Having said that, it is possible to craft a `RunSQL` operation that makes it impossible to determine the desired behaviour. Having an `UPDATE` statement as the last part of a CTE would be a good way to do this.