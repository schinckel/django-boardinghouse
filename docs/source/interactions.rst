===============================
Interaction with other packages
===============================

Because of the way django-boardinghouse patches django, there may be implications for the way other packages behave when both are installed.

South
=====

This is the obvious one, and there is a lot of code within django-boardinghouse that deals with making south work as expected.

Schema Migrations
-----------------

Each call to a database api method (eg ``db.create_table``) is wrapped in a function that will apply the operation to each schema, if the table that is being operated upon belongs to a model that is not a shared model.

However, because we can only look at `current` model structures, if you delete a model that is a shared model, you will need to add it to the ``settings.SHARED_DELETED_TABLES`` to enable the migration to succeed.

Data Migrations
---------------

Each data migration will be run on each schema.

This has some significant implications. You must make sure your migrations are idempotent if they contain any references to shared models: that is, running them several times will not result in undesired behaviour.

If a data migration fails on a subsquent schema application, it may not roll back the changes made to the previous schema(ta).

Django-Reversion
================

It makes sense to have django-reversion store ``Revisions`` and ``Versions`` in each schema. That way you can have per-tenant versioning (which was a primary reason for this project).

.. note::
  This has not yet been implemented:

  However, you may want to have versioning for your shared models. Because of this, the relevant tables will also be created in the ``public`` schema. When creating a version of a model that is a `Shared Model`, you must remember to deactivate any active schema (and then possibly reactivate it).