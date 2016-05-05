from django.apps import apps, AppConfig


class SharedGroupsConfig(AppConfig):
    name = 'boardinghouse.contrib.groups'

    def ready(self):
        from django.conf import settings
        from boardinghouse.signals import session_schema_changed

        User = apps.get_model(settings.AUTH_USER_MODEL)

        self.required_public_views = [
            User.groups.through,
            User.user_permissions.through
        ]

        settings.PRIVATE_MODELS.extend([
            '{m.app_label}.{m.model_name}'.format(m=User.groups.through._meta).lower(),
            '{m.app_label}.{m.model_name}'.format(m=User.user_permissions.through._meta).lower()
        ])

        def flush_user_perms_cache(sender, user, **kwargs):
            if hasattr(user, '_perm_cache'):
                del user._perm_cache

        session_schema_changed.connect(flush_user_perms_cache, weak=False)


class GroupsConfig(SharedGroupsConfig):
    name = 'boardinghouse.contrib.groups'

    def ready(self):
        from django.conf import settings
        from django.contrib.auth.models import Group

        super(GroupsConfig, self).ready()
        settings.PRIVATE_MODELS.append('auth.groups')

        self.required_public_views.extend([
            Group,
            Group.permissions.through
        ])