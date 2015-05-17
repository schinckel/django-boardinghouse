from django.test import TestCase

from boardinghouse.backends.postgres.schema import STATEMENTS

class TestRegexMatches(TestCase):
    def test_drop_trigger(self):
        matcher = STATEMENTS['trigger']
        self.assertIsNotNone(matcher.match('DROP TRIGGER supersede_existing_shift ON roster_shift'))
