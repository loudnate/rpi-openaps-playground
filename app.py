from datetime import timedelta
from dateutil.parser import parse
from flask import Flask
from flask import request
from flask import render_template
from functools import wraps
from subprocess import CalledProcessError
from werkzeug.contrib.cache import SimpleCache

from openapscontrib.mmhistorytools.historytools import CleanHistory
from openapscontrib.mmhistorytools.historytools import ReconcileHistory
from openapscontrib.mmhistorytools.historytools import ResolveHistory
from openapscontrib.mmhistorytools.historytools import NormalizeRecords

from glucodyn import GlucoDynEventHistory
import pump

app = Flask(__name__, static_url_path='')


cache = SimpleCache()


def cached(timeout=5 * 60, key='view/%s'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % request.path
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator


@app.route("/")
@cached(timeout=60)
def glucodyn():
    """Renders a GlucoDyn prediction graph from the current pump settings and recent history"""
    try:
        pump_datetime = parse(pump.read_clock())
        bginitial, glucose_datetime = pump.glucose_level_at_datetime(pump_datetime)

        # Glucodyn template data
        settings = {
            "pump_time_string": glucose_datetime.strftime('%I:%M:%S %p'),
            "cratio": pump.carb_ratio_at_time(glucose_datetime.time()),
            "sensf": pump.insulin_sensitivity_at_time(glucose_datetime.time()),
            "idur": pump.insulin_action_curve(),
            "bginitial": bginitial,
            "stats": 1,
            "inputeffect": 1
        }

        max_carb_absorption = 4
        settings["simlength"] = max(settings["idur"], max_carb_absorption)
        start_datetime = glucose_datetime - timedelta(hours=settings["simlength"])

        pump_history = pump.history_in_range(
            start_datetime,
            glucose_datetime
        )

        basal_schedule = pump.basal_schedule()
    except CalledProcessError as e:
        raise Exception('{} returned status {}: {}'.format(e.cmd, e.returncode, e.output))
    else:
        parser = NormalizeRecords(
            ResolveHistory(
                ReconcileHistory(
                    CleanHistory(pump_history, start_datetime=start_datetime).clean_history
                ).reconciled_history,
                current_datetime=pump_datetime
            ).resolved_records,
            basal_schedule=basal_schedule,
            zero_datetime=glucose_datetime
        )

        gdeh = GlucoDynEventHistory(parser.normalized_records)
        current_basal_rate = parser.basal_rates_in_range(
            pump_datetime.time(),
            (pump_datetime + timedelta(hours=1)).time()
        )[0]

        settings["simlength"] += (gdeh.latest_end_at / 60.0)

        return render_template(
            'glucodyn.html',
            userdata=settings,
            cache_info=pump.cache_info(),
            pump_history=pump_history,
            basal_schedule=basal_schedule,
            uevent=gdeh.uevent,
            current_basal_rate=current_basal_rate
        )

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
