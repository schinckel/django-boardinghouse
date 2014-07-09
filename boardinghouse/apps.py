from django.apps import AppConfig
from django.contrib.auth import get_user_model

from .models import visible_schemata


class BoardingHouseConfig(AppConfig):
    name = 'boardinghouse'

    def ready(self):
        User = get_user_model()
        if not getattr(User, 'visible_schemata', None):
            User.visible_schemata = property(visible_schemata)
