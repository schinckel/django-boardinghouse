import datetime

from django.conf import settings
from django.db import models
from django.utils import six, timezone
from django.utils.functional import cached_property
from django.utils.timesince import timesince, timeuntil
from django.utils.translation import ugettext as _

import pytz

from boardinghouse.base import SharedSchemaMixin
from boardinghouse.exceptions import Forbidden
from boardinghouse.schema import activate_schema, deactivate_schema


class ExpiringObjectsQuerySet(models.query.QuerySet):
    def expired(self):
        "Expired demos"
        return self.filter(expires_at__lt=timezone.now().replace(tzinfo=pytz.utc))

    def active(self):
        "Non-expired demos"
        return self.filter(expires_at__gte=timezone.now().replace(tzinfo=pytz.utc))


@six.python_2_unicode_compatible
class DemoSchema(SharedSchemaMixin, models.Model):
    """A User's demo setup.

    Each user may only have at most one DemoSchema object, which will have an
    expiry date.

    We retain a reference to the template from which it was cloned, so we can
    easily reset it.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                primary_key=True,
                                related_name='demo_schema')
    expires_at = models.DateTimeField()
    from_template = models.ForeignKey('template.SchemaTemplate',
                                      on_delete=models.CASCADE,
                                      related_name='demo_schemata',
                                      limit_choices_to=~models.Q(use_for_demo=None))

    objects = ExpiringObjectsQuerySet.as_manager()

    class Meta:
        verbose_name = 'user demo'
        verbose_name_plural = 'user demos'

    def __str__(self):
        if self.expired:
            return u'Expired demo for {} (expired {} ago)'.format(self.user, timesince(self.expires_at))

        return u'Demo for {}: expires at {} ({} from now)'.format(self.user, self.expires_at, timeuntil(self.expires_at))

    @cached_property
    def schema(self):
        return '{}{}'.format(settings.BOARDINGHOUSE_DEMO_PREFIX, self.user_id)

    @property
    def expired(self):
        return self.expires_at < timezone.now().replace(tzinfo=pytz.utc)

    @property
    def name(self):
        return _('Demo schema ({template_name})').format(template_name=self.from_template.name)

    @property
    def _clone(self):
        return self.from_template.schema

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) + settings.BOARDINGHOUSE_DEMO_PERIOD
        return super(DemoSchema, self).save(*args, **kwargs)

    def activate(self):
        if self.expired:
            raise DemoSchemaExpired()
        activate_schema(self.schema)

    def deactivate(self):
        deactivate_schema()


class DemoSchemaExpired(Forbidden):
    pass


class ValidDemoTemplateManager(models.Manager):
    def get_queryset(self):
        return super(ValidDemoTemplateManager, self).get_queryset().filter(template_schema__is_active=True)


class ValidDemoTemplate(SharedSchemaMixin, models.Model):
    template_schema = models.OneToOneField('template.SchemaTemplate',
                                           primary_key=True,
                                           on_delete=models.CASCADE,
                                           related_name='use_for_demo')

    objects = ValidDemoTemplateManager()

    def __str__(self):
        return '{} is valid as a demo source'.format(self.template_schema)
