import unittest

from django.conf import settings
from django.test import TestCase

from boardinghouse.schema import is_shared_model, is_shared_table

from ..models import *

class TestIsSharedModel(TestCase):
    def test_aware_model(self):
        self.assertFalse(is_shared_model(AwareModel()))

    def test_naive_model(self):
        self.assertTrue(is_shared_model(NaiveModel()))

    def test_self_referential_model(self):
        self.assertFalse(is_shared_model(SelfReferentialModel()))

    def test_co_referential_models(self):
        self.assertFalse(is_shared_model(CoReferentialModelA()))
        self.assertFalse(is_shared_model(CoReferentialModelB()))

    def test_contrib_models(self):
        from django.contrib.admin.models import LogEntry
        from django.contrib.auth.models import User, Group, Permission

        self.assertTrue(is_shared_model(User()))
        self.assertTrue(is_shared_model(Permission()))
        self.assertTrue(is_shared_model(Group()))
        self.assertTrue(is_shared_model(LogEntry()))

class TestIsSharedTable(TestCase):
    def test_schema_table(self):
        self.assertTrue(is_shared_table('boardinghouse_schema'))
        self.assertTrue(is_shared_table('boardinghouse_schema_users'))

    def test_aware_model_table(self):
        self.assertFalse(is_shared_table(AwareModel._meta.db_table))

    def test_naive_model_table(self):
        self.assertTrue(is_shared_table(NaiveModel._meta.db_table))

    def test_join_tables(self):
        self.assertTrue(is_shared_table('auth_group_permissions'))
        self.assertTrue(is_shared_table('auth_user_groups'))
