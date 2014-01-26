Installation/Usage
==================

Requirements
------------

* Django_
* Postgres_
* psycopg2_
* django-model-utils_

This application requires, and depends upon Django_ being installed. Currently, versions from 1.4 are supported. Migration support for 1.7 is under development.
Using Django 1.6 and below with South is also supported.

Postgres is required to allow schema to be used. psycopg2_ is required as per normal Django/Postgres integration.

django-model-utils_ is used for ``PassThroughManager``, which, under Django 1.7 will be replaced by `QuerySet.as_manager() <https://docs.djangoproject.com/en/dev/topics/db/managers/#creating-manager-with-queryset-methods>`_. However, the ``Tracker`` feature is also used to track changes on the :class:`boardinghouse.models.Schema` model, to prevent modification of the `schema` attribute.

Installing
----------

Install it using your favourite installer: mine is `pip`::

    pip install django-boardinghouse

You will need to add ``boardinghouse`` to your ``settings.INSTALLED_APPS``.

If you use South_, you must put it after ``south``. If you use the Django admin, put it before ``django.contrib.admin``. [Check this is still correct under 1.7].

You will need to use the provided database engine::

    'boardinghouse.backends.postgres'

If you are using South, add the following to your settings::

    SOUTH_DATABASE_ADAPTERS = {
        'default': 'boardinghouse.backends.south_backend',
        'boardinghouse.backends.postgres': 'boardinghouse.backends.south_backend',
    }

You will probably want to modify your ``User`` model so it contains a relationship to :class:`boardinghouse.models.Schema`. The type of relationship depends on your business logic.

``django-boardinghouse`` automatically installs a class to your middleware, and a context processor. If you have the admin installed, it adds a column to the admin :class:`django.contrib.admin.models.LogEntry` class, to store the object schema when applicable.

It's probably much easier to start using ``django-boardinghouse`` right from the beginning of a project: trying to split an existing database may be possible, but is not supported at this stage.

Usage
-----

Management commands
~~~~~~~~~~~~~~~~~~~

Once django-boardinghouse hase been installed correctly, it will override some commands related to database access. For instance, in Django <1.7, the ``syncdb`` command is replaced with a version that applies the changes to every known schema. South's ``migrate`` command is likewise overriden.

``loaddata`` and ``dumpdata`` are also overridden. They may take an optional ``--schema`` argument, that will activate that schema before running the command.

Middleware
~~~~~~~~~~



Template Variables
~~~~~~~~~~~~~~~~~~

Changing Schema
~~~~~~~~~~~~~~~



.. _Django: https://www.djangoproject.com/
.. _Postgres: http://www.postgresql.org/
.. _PostgresApp: http://postgresapp.com/
.. _psycopg2: https://pypi.python.org/pypi/psycopg2/
.. _django-model-utils: http://django-model-utils.readthedocs.org
.. _South: http://south.readthedocs.org/
