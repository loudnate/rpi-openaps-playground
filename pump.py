"""
Interface for openaps device "pump"

TODO: Document exceptions
TODO: Caching layer
"""
from datetime import timedelta
from dateutil import parser
import json


def carb_ratio_at_time(pump_time):
    """Returns the carb ratio at a given time of day on the pump clock

    :param pump_time:
    :type pump_time: datetime.time
    :return:
    :rtype: int
    """
    offset_key = "r"
    ratio_key = "i"

    pump_time_minutes = pump_time.hour * 60.0 + pump_time.minute + pump_time.second / 60.0
    pump_time_offset = pump_time_minutes / 30.0

    # TODO: Read carb ratios when decoding-carelink PR #95 is merged
    for schedule in _carb_ratios_dict["schedule"]:
        if schedule[offset_key] == 0 or pump_time_offset < schedule[offset_key]:
            return schedule[ratio_key]


def clock_datetime():
    """Returns the current date and time from the pump's system clock

    :return:
    :rtype: datetime.datetime
    """
    pump_datetime_iso = json.loads(_pump_output("read_clock"))
    return parser.parse(pump_datetime_iso)


def glucose_level_at_pump_datetime(pump_datetime):
    """Returns the most-recent glucose level at a specified time in the sensor history

    Returns None if no glucose readings were recorded in the 15 minutes before `pump_datetime`

    :param pump_datetime:
    :type pump_datetime: datetime.datetime
    :return: The most-recent glucose level (mg/dL), or None
    :rtype: int|NoneType
    """
    glucose_pages_dict = json.loads(
        _pump_output(
            "filter_glucose_date",
            (pump_datetime - timedelta(minutes=15)).isoformat(),
            pump_datetime.isoformat()
        )
    )
    last_page = glucose_pages_dict["end"]
    glucose_history = json.loads(_pump_output("read_glucose_data", str(last_page)))
    current_glucose_dict = next(
        (x for x in reversed(glucose_history) if x["name"] in ("GlucoseSensorData", "CalBGForGH")),
        {}
    )
    return current_glucose_dict.get("sgv", current_glucose_dict.get("amount", None))


def insulin_action_curve():
    """

    :return:
    :rtype: int
    """
    settings_dict = json.loads(_pump_output("read_settings"))
    return settings_dict["insulin_action_curve"]


def insulin_sensitivity_at_time(pump_time):
    """Returns the insulin sensitivity at a given time of day on the pump clock

    :param pump_time:
    :type pump_time: datetime.time
    :return:
    :rtype: int
    """
    insulin_sensitivies_dict = json.loads(_pump_output("read_insulin_sensitivies"))

    # TODO: Support a sensitivity schedule
    return insulin_sensitivies_dict["sensitivities"][0]["sensitivity"]


def _pump_output(*args):
    """Executes an `openaps use` command against the `pump` device

    TODO: Expect `report` calls instead of `use` calls
    TODO: Implement a caching layer with customizable TTL (e.g. clock would need 0)

    :param args:
    :type args: tuple(str)
    :return:
    :rtype: str
    """
    from subprocess import check_output

    args_list = ["openaps", "use", "pump"]
    args_list.extend(args)

    return check_output(args_list)


_carb_ratios_dict = {
    "units": "grams",
    "first": 1,
    "schedule": [
        {
            "i": 10,        # Actual ratio value
            "x": 0,         # 0-based index
            "r": 23,        # Actual offset value for the next record, in 30 minute increments
            "ratio": 23,    # Actual offset value for the next record, in 30 minute increments
            "offset": 300   # i * 30 (not useful)
        },
        {
            "i": 8,
            "x": 1,
            "r": 36,
            "ratio": 36,
            "offset": 240
        },
        {
            "i": 6,
            "x": 2,
            "r": 45,
            "ratio": 45,
            "offset": 180
        },
        {
            "i": 10,
            "x": 3,
            "r": 0,
            "ratio": 0,
            "offset": 300
        },
        {
            "i": 0,
            "x": 4,
            "r": 0,
            "ratio": 0,
            "offset": 0
        },
        {
            "i": 0,
            "x": 5,
            "r": 0,
            "ratio": 0,
            "offset": 0
        },
        {
            "i": 0,
            "x": 6,
            "r": 0,
            "ratio": 0,
            "offset": 0
        }
    ]
}
