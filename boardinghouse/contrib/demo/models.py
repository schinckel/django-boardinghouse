import datetime

from django.conf import settings
from django.db import models
from django.utils import six, timezone
from django.utils.timesince import timesince, timeuntil
from django.utils.translation import ugettext as _

from boardinghouse.base import SharedSchemaMixin
from boardinghouse.schema import activate_schema, deactivate_schema
from boardinghouse.schema import Forbidden


class ExpiringObjectsQuerySet(models.query.QuerySet):
    def expired(self):
        return self.filter(expires_at__lt=timezone.now())

    def active(self):
        return self.filter(expires_at__gte=timezone.now())

    def create(self, **kwargs):
        if 'expires_at' not in kwargs:
            kwargs['expires_at'] = datetime.datetime.utcnow() + settings.BOARDINGHOUSE_DEMO_PERIOD
        return super(ExpiringObjectsQuerySet, self).create(**kwargs)


@six.python_2_unicode_compatible
class DemoSchema(SharedSchemaMixin, models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                primary_key=True,
                                related_name='demo_schema')
    expires_at = models.DateTimeField()

    objects = ExpiringObjectsQuerySet.as_manager()

    class Meta:
        verbose_name = 'user demo'
        verbose_name_plural = 'user demos'

    def __str__(self):
        if self.expired:
            return u'Expired demo for {} (expired {} ago)'.format(self.user, timesince(self.expires_at))

        return u'Demo for {}: expires at {} ({} from now)'.format(self.user, self.expires_at, timeuntil(self.expires_at))

    @property
    def schema(self):
        return '{}{}'.format(settings.BOARDINGHOUSE_DEMO_PREFIX, self.user_id)

    @property
    def expired(self):
        return self.expires_at < timezone.now()

    @property
    def name(self):
        return _('Demo schema')

    def activate(self):
        if self.expired:
            raise DemoSchemaExpired()
        activate_schema(self.schema)

    def deactivate(self):
        deactivate_schema()


class DemoSchemaExpired(Forbidden):
    pass


class ValidDemoTemplate(models.Model):
    template_schema_id = models.OneToOneField('template.SchemaTemplate',
                                              primary_key=True,
                                              on_delete=models.CASCADE)
