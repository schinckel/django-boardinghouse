"""
Signals that are fired as part of the django-boardinghouse project.

.. data:: schema_created

.. data:: schema_pre_activate

.. data:: schema_post_activate

"""

from django.dispatch import Signal

schema_created = Signal(providing_args=["schema"])

schema_pre_activate = Signal(providing_args=["schema"])
schema_post_activate = Signal(providing_args=["schema"])

session_requesting_schema_change = Signal(providing_args=["user"])