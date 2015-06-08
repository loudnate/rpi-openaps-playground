from datetime import time
import json
import os
import sys
import unittest
from glucodyn import GlucoDynEventHistory


def get_file_at_path(path):
    return '{}/{}'.format(os.path.dirname(os.path.realpath(sys.argv[0])), path)


class GlucoDynEventHistoryTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(get_file_at_path('fixtures/basal.json')) as fp:
            cls.basal_rate_schedule = json.load(fp)

    def test_basal_rates_in_range(self):
        geh = GlucoDynEventHistory([], self.basal_rate_schedule)

        self.assertListEqual(
            self.basal_rate_schedule,
            geh.basal_rates_in_range(time(0, 0), time(23, 59))
        )

        self.assertListEqual(
            self.basal_rate_schedule[0:1],
            geh.basal_rates_in_range(time(0, 0), time(1, 0))
        )

        self.assertListEqual(
            self.basal_rate_schedule[1:3],
            geh.basal_rates_in_range(time(4, 0), time(9, 0))
        )

        self.assertListEqual(
            self.basal_rate_schedule[5:6],
            geh.basal_rates_in_range(time(16, 0), time(20))
        )

        with self.assertRaises(AssertionError):
            geh.basal_rates_in_range(time(4), time(4))

        with self.assertRaises(AssertionError):
            geh.basal_rates_in_range(time(4), time(3))


if __name__ == '__main__':
    unittest.main()
