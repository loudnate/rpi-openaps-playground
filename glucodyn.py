"""
Model generator for GlucoDyn event history
"""
from collections import defaultdict
from datetime import datetime
from datetime import timedelta


class GlucoDynEventHistory(object):
    def __init__(self, pump_history, zero_datetime=None):
        self.uevent = []
        self.raw = pump_history
        self.zero_datetime = zero_datetime or datetime.now()

        self._boluswizard_events_by_body = defaultdict(list)

        for event in pump_history:
            try:
                decoded = getattr(self, "_decode_{}".format(event["_type"].lower()))(event)
            except AttributeError:
                pass
            else:
                if decoded is not None:
                    self.uevent.append(decoded)

    def _relative_time(self, timestamp):
        return int(round((timestamp - self.zero_datetime).total_seconds() / 60))

    def _decode_bolus(self, event):
        if event["type"] == "square":
            t0 = self._relative_time(event["timestamp"])
            duration = event["duration"]
            delivered = event["amount"]
            programmed = event["programmed"]
            rate = programmed / duration  # U/min

            # If less than 100% of the programmed dose was delivered and we're past the delivery
            # window, then estimate the actual duration.
            if t0 + duration < 0:
                duration = int(duration * delivered / programmed)

            return {
                "etype": "tempbasal",
                "time": t0,
                "t1": t0,
                "t2": t0 + duration,
                "dbdt": rate
            }
        elif event["amount"] > 0:
            return {
                "etype": "bolus",
                "time": self._relative_time(event["timestamp"]),
                "units": event["amount"]
            }

    def _decode_boluswizard(self, event):
        # BolusWizard records can appear as duplicates with one containing appended data.
        # Criteria are records are less than 1 min apart and have identical bodies
        for seen_event in self._boluswizard_events_by_body[event["_body"]]:
            if abs(seen_event["timestamp"] - event["timestamp"]) <= timedelta(minutes=1):
                return None

        self._boluswizard_events_by_body[event["_body"]].append(event)

        return {
            "etype": "carb",
            "ctype": 180,  # Absorption rate. "Low": 240, "High": 90
            "time": self._relative_time(event["timestamp"]),
            "grams": event["carb_input"]
        }

    _decode_journalentrymealmarker = _decode_boluswizard

    # TODO: Suspend/Resume as TempBasal
    # TODO: TempBasal
