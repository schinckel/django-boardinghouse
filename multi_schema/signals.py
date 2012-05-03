from django.dispatch import Signal

schema_created = Signal(providing_args=["schema"])

schema_pre_activate = Signal(providing_args=["schema"])
schema_post_activate = Signal(providing_args=["schema"])
