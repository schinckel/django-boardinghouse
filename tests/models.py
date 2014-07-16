from django.db import models
from django.contrib.auth.models import User  # NOQA

from boardinghouse.base import SharedSchemaModel, MultiSchemaManager


class AwareModel(models.Model):
    name = models.CharField(max_length=10, unique=True)
    status = models.BooleanField(default=False)

    objects = MultiSchemaManager()

    class Meta:
        app_label = 'tests'


class NaiveModel(SharedSchemaModel):
    name = models.CharField(max_length=10, unique=True)
    status = models.BooleanField(default=False)

    class Meta:
        app_label = 'tests'


# The existence of this model, although it may not have tests
# that apply to it, is enough to trigger infinite recursion if
# a check for self-referencing models is not made in is_shared_model()
class SelfReferentialModel(models.Model):
    name = models.CharField(max_length=10, unique=True)
    parent = models.ForeignKey('tests.SelfReferentialModel', related_name='children', null=True, blank=True)

    class Meta:
        app_label = 'tests'


# If you have two models that _only_ have foreign keys, and they happen
# to include references to one another, then you could get an infinite
# recursion. However, I can't see that this model structure makes sense.
class CoReferentialModelA(models.Model):
    name = models.CharField(max_length=10, unique=True)
    other = models.ForeignKey('tests.CoReferentialModelB', related_name='model_a', null=True, blank=True)

    class Meta:
        app_label = 'tests'


class CoReferentialModelB(models.Model):
    name = models.CharField(max_length=10, unique=True)
    other = models.ForeignKey('tests.CoReferentialModelA', related_name='model_b', null=True, blank=True)

    class Meta:
        app_label = 'tests'
