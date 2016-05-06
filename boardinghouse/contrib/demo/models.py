import datetime

from django.conf import settings
from django.db import models

from boardinghouse.base import SharedSchemaMixin
from boardinghouse.schema import activate_schema, deactivate_schema
from boardinghouse.schema import Forbidden


class ExpiringObjectsQuerySet(models.query.QuerySet):
    def expired(self):
        return self.filter(expiry_date__lt=datetime.datetime.utcnow())

    def active(self):
        return self.filter(expiry_date__gte=datetime.datetime.utcnow())

    def create(self, **kwargs):
        if 'expiry_date' not in kwargs:
            kwargs['expiry_date'] = datetime.datetime.utcnow() + datetime.timedelta(31)
            # kwargs['expiry_date'] = datetime.datetime.utcnow() + settings.BOARDINGHOUSE_DEMO_PERIOD
        return super(ExpiringObjectsQuerySet, self).create(**kwargs)


class DemoSchema(SharedSchemaMixin, models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                primary_key=True,
                                related_name='demo_schema')
    expiry_date = models.DateTimeField()

    objects = ExpiringObjectsQuerySet.as_manager()

    @property
    def schema(self):
        return '__demo_{}'.format(self.user_id)

    def activate(self):
        if self.expiry_date < datetime.datetime.utcnow():
            raise DemoSchemaExpired()
        activate_schema(self.schema)

    def deactivate(self):
        deactivate_schema()


class DemoSchemaExpired(Forbidden):
    pass
