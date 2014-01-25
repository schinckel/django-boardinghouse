Installation
============

Requirements
------------

* Django_
* Postgres_
* psycopg2_
* django-model-utils_

This application requires, and depends upon Django being installed. Currently, versions from 1.4 are supported. Migration support for 1.7 is under development.
Using Django 1.6 and below with South is also supported.

Postgres is required to allow schema to be used. ``psycopg2`` is required as per normal Django/Postgres integration.

django-model-utils_ is used for ``PassThroughManager``, which, under Django 1.7 will be replaced by `QuerySet.as_manager() <https://docs.djangoproject.com/en/dev/topics/db/managers/#creating-manager-with-queryset-methods>`_. However, the ``Tracker`` feature is also used to track changes on the :class:`Schema` model, to prevent modification of the `schema` attribute.

Installing
----------

Install it using your favourite installer: mine is `pip`::

    pip install django-boardinghouse

You will need to add ``boardinghouse`` to your ``settings.INSTALLED_APPS``.

If you use ``south``, put it after that. If you use the Django admin, put it before that. [Check this is still correct under 1.7].

You will need to use the provided database engine::

    boardinghouse.backends.postgres

If you are using South, add the following to your settings::

    SOUTH_DATABASE_ADAPTERS = {
        'default': 'boardinghouse.backends.south_backend',
        'boardinghouse.backends.postgres': 'boardinghouse.backends.south_backend',
    }

You will probably want to modify your ``User`` model so it contains a relationship to ``Schema``. The type of relationship depends on your business logic.

``django-boardinghouse`` automatically installs a class to your middleware, and a context processor. If you have the admin installed, it adds a column to the admin ``LogEntry`` class, to store the object schema when applicable.

It's probably much easier to start using ``django-boardinghouse`` right from the beginning of a project: trying to split an existing database may be possible, but is not supported at this stage.