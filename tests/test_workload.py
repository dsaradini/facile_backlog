from django.test import TestCase

from facile_backlog.core.workload import to_string, parse


class WorkloadTest(TestCase):

    def test_workload_format(self):
        self.assertEqual(
            to_string(60*60*300), "300 hours"
        )

        self.assertEqual(
            to_string(60*60*300, 60*60*10), "30 days"
        )

        self.assertEqual(
            to_string((60*60*300) + 23), "300 hours, 23 seconds"
        )

        self.assertEqual(
            to_string((60*60*300) + (23*60)), "300 hours, 23 minutes"
        )

        self.assertEqual(
            to_string((60*60*301) + (23*60), (60*60*10)),
            "30 days, 1 hour, 23 minutes"
        )

        self.assertEqual(
            to_string((60*60*302) + (23*60) + 1, (60*60*10)),
            "30 days, 2 hours, 23 minutes, 1 second"
        )

        self.assertEqual(
            to_string(-60*60*300), "-300 hours"
        )

    def test_workload_parse(self):
        self.assertEqual(
            parse("300 hours"), 60*60*300
        )
        self.assertEqual(
            parse("30 days", 60*60*10), 60*60*300
        )
        self.assertEqual(
            parse("1:30", 60*60*10), 3600 + (30*60)
        )
