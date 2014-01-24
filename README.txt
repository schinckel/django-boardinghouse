Django Boardinghouse
====================

Use `Postgres Schemas`_ for `multi-tenant applications <http://en.wikipedia.org/wiki/Multitenancy>`_ (or other segmenting).

.. image:: https://drone.io/bitbucket.org/schinckel/django-boardinghouse/status.png
.. image:: https://drone.io/bitbucket.org/schinckel/django-boardinghouse/files/.coverage/coverage_status.png

Philosophy
----------

In a multi-tenancy environment, there are three possible setups.

1. Everything is in the one database/schema.
  
  A reliance on Foreign Keys to a table that contains the different tenants (customers, companies, organisations, whatever they are called in your database). 
  
  Everyone accesses the system in the same way (using the same url), and their user credentials associate them with one or more tenancies.

2. Everything is in it's own database or schema. 

  A truly siloed approach, where nothing is shared between tenants. Good in it's own way, but means that you can't associate one user account with multiple tenancies (or you could, but you'd need to push user data between systems, including passwords). 
  
  You could have totally different servers/instances of the web application/site on the one server. This would traditionally be a multi-instance setup, although you could do it with one application instance.

  Often, you would have each tenant with their own domain name, and the incoming request is pushed to the right instance/tenant based upon that.

3. Some models should be partitioned between schemata, others should be global (public schema). 
  
  Anything which is specific to a single tenant is stored in that silo, everything that should be global is stored in the public schema.

This project provides a solution for situation 3. The intention of this project would be where Users:

* have a relationship to a schema, and when they view a page, it automatically only fetches data that is from their schema.

* may belong to multiple schemata, and should be a mechanism for switching between them.

This has some advantages. Primarily, data can never leak between schemata, it no longer relies on thorough foreign key checking.

More so, I've noticed in my work that I need to be able to report on data from a single tenant, and having to trace back relations to find the tenancy table relation (or having a relationship in every table) makes writing these reports hard. For instance, fetching a `django-reversion`_ report for a single customer's data is nigh-on impossible.


How it works
------------

There is a special model: ``Schema``. Whenever new instances of this model are created, the system creates a Postgres schema with that name. There is a special ``__template__`` schema, that stores an empty copy of the schema, and the new schema is defined according to that.

Whenever a ``syncdb`` or ``migrate`` happens, we repeat all of the changes to each schema.

Whenever a request comes in, some middleware determines which schema should be active, and sets the postgres ``search_path`` accordingly. Some users may be able to request a different schema to be activated, and if they have the permission, they will then see data from that schema.

Requirements
------------

* Django_
* Postgres_/psycopg2_
* django-model-utils_

This only works with, and required Django_. Currently, versions 1.4.x, 1.5.x and 1.6.x are automatically tested. If you are using these versions, you may use South_ for migrations: migrations will be run against all existing schemata. Some support for Django 1.7 exists, however migration support is untested.

Since this uses Postgres Schemata for partitioning, you will need Postgres_ installed. You will want to use psycopg2_ to connect to that. I've been using PostgresApp_ to run Postgres easily on my Mac.

django-model-utils_ is being used for ``PassThroughManager`` (which, under Django 1.7 will be replaced by the inbuilt `QuerySet.as_manager() <https://docs.djangoproject.com/en/dev/topics/db/managers/#creating-manager-with-queryset-methods>`_ feature.)

Added neat features (hacks)
---------------------------

Admin users can change to view any schema. There is an added selector in the brand bar for this. You will only see items from the currently selected schema in the admin change list views, and you cannot change schema when viewing an object (as ids are unique across schemata).

I've hacked in support in admin.LogEntry to store the schema on a log when there is a schema associated with the model. The links that are generated (that you see in the recent actions, for instance) contain a url fragment to switch to the correct schema, so they still work.

``./manage.py dumpdata`` and ``loaddata`` gain a ``--schema`` keyword. It defaults to ``__template__``, which is a special empty template. Data will only be dumped-from/loaded-to the selected schema (or public, if the objects are not schema-aware). Data will *not* be written to ``__template__``, instead an error will be thrown.


TODOs
-----

* Cache schema queryset so we don't have to load it each request. We would need to invalidate this cache when a new schema is added.

* Cache request.user.schemata queryset (as above).

* Provide a better error when ``loaddata`` is run without ``--schema``, and an error occurred.

* Use the ``schema`` attribute on serialised objects to load them into the correct schema. I think this is possible.

* Write more tests

  * test migrations under south
  * test migrations under django1.7
  * test ensure_installation
  

* Create an example project (maybe part of tests?)

* Enable support for django-devserver: we currently get an infinite recursion when both of us are installed.

* Prevent admin access to pages requiring schema selection when no schema is selected.

* Bounce to a reasonable page when a schema change event is processed, and the current page is no longer valid in the new schema. For instance, if viewing schema aware data at:

    https://example.com/photos/223/

  And then changing schema, it probably should show the list of photos, rather than photo with that id in the new schema.

Installation Instructions
-------------------------

You need to do the following to install `django-boardinghouse`.

* Install it into your virtualenv.
* Add ``'boardinghouse'`` to your ``settings.INSTALLED_APPS`` (after ``south`` if you have that installed, and before ``django.contrib.admin``).
* Set your Database Engine(s) to ``'boardinghouse.backends.postgres'``
* Add the following to your settings (if using south):: 

    SOUTH_DATABASE_ADAPTERS = {
        'default': 'boardinghouse.backends.south_backend',
        'boardinghouse.backends.postgres': 'boardinghouse.backends.south_backend',
    }

* Modify your user model so it contains a relationship to ``Schema`` (the type of relationship will depend upon your business logic).

``django-boardinghouse`` automatically installs a class to your middleware, and a context processor. If you have the admin installed, it adds a column to the admin ``LogEntry`` class, to store the object schema when applicable.

It's probably much easier to start using ``django-boardinghouse`` right from the beginning of a project: trying to split an existing database may be possible, but is not supported at this stage.


Development
-----------

You can run tests across all supported versions using tox_. Make sure you have a checked-out version of the project from:

https://bitbucket.org/schinckel/django-boardinghouse/

If you have tox installed, then you'll be able to run it from the checked out directory.

Bugs and feature requests can be reported on BitBucket, and Pull Requests may be accepted.


.. _Django: http://www.djangoproject.com/
.. _Postgres: http://www.postgresql.org/
.. _PostgresApp: http://postgresapp.com/
.. _psycopg2: https://pypi.python.org/pypi/psycopg2/
.. _django-model-utils: http://django-model-utils.readthedocs.org
.. _South: http://south.readthedocs.org/
.. _tox: http://tox.readthedocs.org
.. _Postgres Schemas: http://www.postgresqlforbeginners.com/2010/12/schema.html
.. _django-reversion: http://django-reversion.readthedocs.org