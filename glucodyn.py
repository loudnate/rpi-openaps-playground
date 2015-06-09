"""
Model generator for GlucoDyn event history
"""
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from dateutil import parser


class GlucoDynEventHistory(object):
    def __init__(self, pump_history, basal_schedule, zero_datetime=None, sim_hours=4):
        self.uevent = []
        self.raw = pump_history
        self.zero_datetime = zero_datetime or datetime.now()
        self.sim_hours = sim_hours
        self.basal_schedule = basal_schedule

        # Temporary parsing state
        self._boluswizard_events_by_body = defaultdict(list)
        self._suspend_datetime = None
        self._last_temp_basal_event = None

        for event in pump_history:
            self.add_history_event(event)

        # The pump is still suspended
        if self._suspend_datetime is not None:
            self.add_history_event({
                "_type": "PumpResume",
                "timestamp": zero_datetime
            })

    def add_history_event(self, event):
        try:
            decoded = getattr(self, "_decode_{}".format(event["_type"].lower()))(event)
        except AttributeError:
            pass
        else:
            self.uevent.extend(decoded or [])

    def basal_rates_in_range(self, start_time, end_time):
        """Returns a list of the current basal rates effective between the specified times

        :param start_time:
        :type start_time: datetime.time
        :param end_time:
        :type end_time: datetime.time
        :return: A list of basal rates
        :rtype: list(dict)
        """
        assert(start_time < end_time)

        start_index = 0
        end_index = len(self.basal_schedule)

        for index, basal_rate in enumerate(self.basal_schedule):
            basal_start_time = parser.parse(basal_rate["start"]).time()
            if start_time >= basal_start_time:
              start_index = index
            if end_time < basal_start_time:
              end_index = index
              break

        return self.basal_schedule[start_index:end_index]

    def _basal_adjustments_in_range(self, start_datetime, end_datetime, percent=None, rate=None):
        """Returns a list of tempbasal events representing the requested adjustment to the pump's basal schedule

        :param start_datetime:
        :type start_datetime: datetime
        :param end_datetime:
        :type end_datetime: datetime
        :param percent: A multiplier to apply to the current basal rate
        :type percent: int
        :param rate: A specified temporary basal rate, in U/hour
        :type rate: float
        :return: A list of tempbasal events
        :rtype: list(dict)

        :raises AssertionError: The arguments are either missing or invalid
        """
        assert(start_datetime < end_datetime)
        assert(end_datetime - start_datetime < timedelta(hours=24))
        assert(percent is not None or rate is not None)

        start_time = start_datetime.time()
        end_time = end_datetime.time()

        # If the requested timestamps cross a day boundary, return the combination of each single-day call
        if start_time > end_time:
            return self._basal_adjustments_in_range(
                    start_datetime,
                    start_datetime.replace(hour=23, minute=59, second=59),
                    percent=percent,
                    rate=rate
                ) + \
                self._basal_adjustments_in_range(
                    end_datetime.replace(hour=0, minute=0, second=0),
                    end_datetime,
                    percent=percent,
                    rate=rate
                )

        temp_basal_events = []
        basal_rates = self.basal_rates_in_range(start_time, end_time)

        for index, basal_rate in enumerate(basal_rates):
            basal_start_time = parser.parse(basal_rate["start"]).time()

            # If we are in a list longer than one element, adjust the boundary timestamps to the basal time
            if index > 0:
                if start_time <= basal_start_time:
                    t0 = datetime.combine(start_datetime.date(), basal_start_time)
                else:
                    t0 = datetime.combine(end_datetime.date(), basal_start_time)
                t0 = self._relative_time(t0)
                temp_basal_events[-1]["t2"] = t0
            else:
                t0 = self._relative_time(start_datetime)

            t1 = self._relative_time(end_datetime)
            event = {
                "etype": "tempbasal",
                "time": t0,
                "t1": t0,
                "t2": t1
            }

            # Find the delta of the new rate
            new_rate = rate
            if percent is not None:
                new_rate = basal_rate["rate"] * percent / 100.0

            event["dbdt"] = (new_rate - basal_rate["rate"]) / 60.0

            temp_basal_events.append(event)

        return temp_basal_events

    def _relative_time(self, timestamp):
        return int(round((timestamp - self.zero_datetime).total_seconds() / 60))

    def _decode_bolus(self, event):
        if event["type"] == "square":
            t0 = self._relative_time(event["timestamp"])
            duration = event["duration"]
            delivered = event["amount"]
            programmed = event["programmed"]
            rate = programmed / 60.0  # U/min

            # If less than 100% of the programmed dose was delivered and we're past the delivery
            # window, then estimate the actual duration.
            if t0 + duration < 0:
                duration = int(duration * delivered / programmed)

            return [{
                "etype": "tempbasal",
                "time": t0,
                "t1": t0,
                "t2": t0 + duration,
                "dbdt": rate
            }]
        elif event["amount"] > 0:
            return [{
                "etype": "bolus",
                "time": self._relative_time(event["timestamp"]),
                "units": event["amount"]
            }]

    def _decode_boluswizard(self, event):
        # BolusWizard records can appear as duplicates with one containing appended data.
        # Criteria are records are less than 1 min apart and have identical bodies
        for seen_event in self._boluswizard_events_by_body[event["_body"]]:
            if abs(seen_event["timestamp"] - event["timestamp"]) <= timedelta(minutes=1):
                return None

        self._boluswizard_events_by_body[event["_body"]].append(event)

        return self._decode_journalentrymealmarker(event)

    def _decode_journalentrymealmarker(self, event):
        if event["carb_input"] > 0:
            return [{
                "etype": "carb",
                "ctype": 180,  # Absorption rate. "Low": 240, "High": 90
                "time": self._relative_time(event["timestamp"]),
                "grams": event["carb_input"]
            }]

    def _decode_pumpresume(self, event):
        start_datetime = self._suspend_datetime or (self.zero_datetime - timedelta(hours=self.sim_hours))
        return self._basal_adjustments_in_range(start_datetime, event["timestamp"], percent=0)

    def _decode_pumpsuspend(self, event):
        self._suspend_datetime = event["timestamp"]

    def _decode_tempbasal(self, event):
        # Since only one tempbasal runs at a time, we have to consider the cancellation event, which is logged as a "0" rate and "0" duration
        pass

    def _decode_tempbasalduration(self, event):
        pass
