from django.apps import AppConfig

from .models import add_visible_schemata_to_user

class BoardingHouseConfig(AppConfig):
    name = 'boardinghouse'
    
    def ready(self):
        add_visible_schemata_to_user()