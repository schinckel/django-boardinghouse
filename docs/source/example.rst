========
Examples
========

Boarding School
===============

Technically, this example has nothing to do with an *actual* boarding school, it just seemed like a clever name for a project based on a school.

This project provides a simple working example of a multi-tenanted django project using django-boardinghouse.

To set up and run project::

  cd examples/boarding_school
  make all

This will create the database, install the requirements, and set up some example data.

When this is complete, you'll want to start up a server::

  ./manage.py runserver 127.0.0.1:8088

Finally, visit http://127.0.0.1:8088/admin/ and log in with username `admin`, password `password`. There is a fully functioning django project, with two schemata (schools) installed, and a smattering of data.

You can see that visiting a model that is split across schemata only shows objects from the current schema, and changing the visible schema will reload the page with the new data.

Also note that it's not possible to change the schema when viewing an object that belongs to a schema.

At this stage, all of the functionality is contained within the admin interface.