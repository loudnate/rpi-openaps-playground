from datetime import datetime
from datetime import time
from dateutil import parser
import json
import os
import sys
import unittest
from glucodyn import GlucoDynEventHistory


def get_file_at_path(path):
    return "{}/{}".format(os.path.dirname(os.path.realpath(sys.argv[0])), path)


def hydrate_event(event):
    event["timestamp"] = parser.parse(event["timestamp"])
    return event


class GlucoDynEventHistoryTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(get_file_at_path("fixtures/basal.json")) as fp:
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

    def test_basal_adjustments_in_range(self):
        geh = GlucoDynEventHistory(
            [],
            self.basal_rate_schedule,
            zero_datetime=datetime(2015, 01, 01, 12)
        )

        with self.assertRaises(AssertionError):
            geh._basal_adjustments_in_range(
                datetime(2015, 01, 02),
                datetime(2015, 01, 01),
                percent=100
            )

        with self.assertRaises(AssertionError):
            geh._basal_adjustments_in_range(
                datetime(2015, 01, 01),
                datetime(2015, 01, 02, 4),
                percent=100
            )

        with self.assertRaises(AssertionError):
            geh._basal_adjustments_in_range(datetime(2015, 01, 01), datetime(2015, 01, 01, 4))

        basal = {
            "etype": "tempbasal",
            "time": -420,
            "t1": -420,
            "t2": -360,
            "dbdt": 0.925 / 60
        }

        self.assertDictEqual(
            basal,
            geh._basal_adjustments_in_range(
                datetime(2015, 01, 01, 05),
                datetime(2015, 01, 01, 06),
                percent=200
            )[0]
        )

        self.assertDictEqual(
            basal,
            geh._basal_adjustments_in_range(
                datetime(2015, 01, 01, 05),
                datetime(2015, 01, 01, 06),
                absolute=1.85
            )[0]
        )

        self.assertListEqual(
            [
                {
                    "etype": "tempbasal",
                    "time": 11 * 60,
                    "t1": 11 * 60,
                    "t2": 12 * 60,
                    "dbdt": -0.45 / 60
                },
                {
                    "etype": "tempbasal",
                    "time": 12 * 60,
                    "t1": 12 * 60,
                    "t2": 14 * 60,
                    "dbdt": -0.45 / 60
                }
            ],
            geh._basal_adjustments_in_range(
                datetime(2015, 01, 01, 23),
                datetime(2015, 01, 02, 02),
                percent=50
            )
        )

    def test_duplicate_bolus_wizard_carbs(self):
        with open(get_file_at_path("fixtures/bolus_wizard_duplicates.json")) as fp:
            pump_history = map(hydrate_event, json.load(fp))

        geh = GlucoDynEventHistory(
            pump_history,
            self.basal_rate_schedule,
            zero_datetime=datetime(2015, 6, 5, 19)
        )

        self.assertListEqual(
            [
                {
                    "etype": "carb",
                    "ctype": 180,
                    "time": -3,
                    "grams": 10
                },
                {
                    "etype": "carb",
                    "ctype": 180,
                    "time": -5,
                    "grams": 30
                },
                {
                    "etype": "carb",
                    "ctype": 180,
                    "time": -15,
                    "grams": 65
                },
            ],
            [event for event in geh.uevent if event["etype"] == "carb"]
        )

    def test_temp_basal(self):
        pump_history = [
            {
                "_body": "",
                "_date": "4a810e050f",
                "_description": "TempBasalDuration 2015-06-05T14:01:10 head[2], body[0] op[0x16]",
                "_head": "1604",
                "_type": "TempBasalDuration",
                "date": 1433509270000.0,
                "duration (min)": 120,
                "timestamp": datetime(2015, 6, 5, 14, 1, 10)
            },
            {
                "_body": "08",
                "_date": "4a810e050f",
                "_description": "TempBasal 2015-06-05T14:01:10 head[2], body[1] op[0x33]",
                "_head": "338c",
                "_type": "TempBasal",
                "date": 1433509270000.0,
                "rate": 140,
                "temp": "percent",
                "timestamp": datetime(2015, 6, 5, 14, 1, 10)
            }
        ]

        geh = GlucoDynEventHistory(
            pump_history,
            self.basal_rate_schedule,
            zero_datetime=datetime(2015, 6, 5, 14)
        )

        self.assertListEqual(
            [
                {
                    "etype": "tempbasal",
                    "time": 1,
                    "t1": 1,
                    "t2": 60,
                    "dbdt": 0.4*0.75/60
                },
                {
                    "etype": "tempbasal",
                    "time": 60,
                    "t1": 60,
                    "t2": 121,
                    "dbdt": 0.4*0.8/60
                }
            ],
            geh.uevent
        )

if __name__ == "__main__":
    unittest.main()
