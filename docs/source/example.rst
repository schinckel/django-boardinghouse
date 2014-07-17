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

When prompted, you will need to create a superuser. Then::

  ./manage.py runserver 127.0.0.1:8088

Finally, visit http://127.0.0.1:8088/admin/ and log in with your superuser's credentials. There is a fully functioning django project, with two schemata (schools) installed, and a smattering of data.

At this stage, all of the functionality is contained within the admin interface.