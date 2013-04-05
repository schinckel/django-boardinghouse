Django Multi-Schema
====================

Use Postgres Schemas for multi-tenant applications (or other segmenting).



Philosophy
----------

Some models should be seperated, others should be global.


Users belong to a schema, and when they view a page, it automatically only fetches data that is from their schema.



How it works
------------

There is a special model: ``Schema``. Whenever new instances of this model are created, the system creates a Postgres schema with that name. There is a special ``__template__`` schema, that stores an empty copy of the schema, and the new schema is defined according to that.

Whenever a ``syncdb`` or ``migrate`` happens, we repeat all of the changes to each schema.

Whenever a user logs in, some middleware determines which schema should be active, and sets the postgres ``search_path`` accordingly. Some users may be able to request a different schema to be activated, and if they have the permission, they will then see data from that schema.


