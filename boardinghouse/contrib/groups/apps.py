from django.apps import AppConfig


class GroupsConfig(AppConfig):
    name = 'boardinghouse.contrib.groups'

    def ready(self):
        from django.conf import settings
        from django.contrib.auth.models import Group

        settings.PRIVATE_MODELS.append('auth.groups')

        self.required_public_views = [
            Group,
            Group.permissions.through
        ]
