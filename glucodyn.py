"""
Model generator for GlucoDyn event history
"""
from openapscontrib.mmhistorytools.models import Unit


# Event keys
_AMOUNT = "amount"
_CTYPE = "ctype"
_DBDT = "dbdt"
_DESCRIPTION = "description"
_END_AT = "end_at"
_ETYPE = "etype"
_GRAMS = "grams"
_START_AT = "start_at"
_T0 = "t1"
_T1 = "t2"
_TIME = "time"
_UNIT = "unit"
_UNITS = "units"


class GlucoDynEventHistory(object):
    def __init__(self, pump_records):
        """Initializes a new instance of a GlucoDyn event history log

        :param pump_records: A list of normalized history events, in reverse-chronological order
        :type pump_records: list(dict)
        """
        self.uevent = []
        self.latest_end_at = 0
        self.raw = pump_records

        for event in pump_records:
            self.uevent.append(self.encode_history_event(event))

    def encode_history_event(self, event):
        start_at = event[_START_AT]
        end_at = event[_END_AT]
        amount = event[_AMOUNT]
        unit = event[_UNIT]
        description = event[_DESCRIPTION]

        if end_at > self.latest_end_at:
            self.latest_end_at = end_at

        if unit == Unit.units_per_hour:
            return {
                _ETYPE: "tempbasal",
                _TIME: start_at,
                _T0: start_at,
                _T1: end_at,
                _DBDT: amount / 60.0,  # U/hour -> U/min
                _DESCRIPTION: description
            }
        elif unit == Unit.units:
            return {
                _ETYPE: "bolus",
                _TIME: start_at,
                _UNITS: amount,
                _DESCRIPTION: description
            }
        elif unit == Unit.grams:
            return {
                _ETYPE: "carb",
                _CTYPE: 180,  # Absorption rate. "Low": 240, "High": 90
                _TIME: start_at,
                _GRAMS: amount,
                _DESCRIPTION: description
            }
