from datetime import timedelta
from dateutil.parser import parse
from flask import Flask
from flask import render_template
from subprocess import CalledProcessError

from openapscontrib.mmhistorytools.historytools import CleanHistory
from openapscontrib.mmhistorytools.historytools import ReconcileHistory
from openapscontrib.mmhistorytools.historytools import ResolveHistory
from openapscontrib.mmhistorytools.historytools import NormalizeRecords

from glucodyn import GlucoDynEventHistory
import pump

app = Flask(__name__, static_url_path='')


@app.route("/")
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
        records = NormalizeRecords(
            ResolveHistory(
                ReconcileHistory(
                    CleanHistory(pump_history, start_datetime=start_datetime).clean_history
                ).reconciled_history,
                current_datetime=pump_datetime
            ).resolved_records,
            basal_schedule=basal_schedule,
            zero_datetime=glucose_datetime
        ).normalized_records

        uevent = GlucoDynEventHistory(records).uevent

        return render_template(
            'glucodyn.html',
            userdata=settings,
            cache_info=pump.cache_info(),
            pump_history=pump_history,
            basal_schedule=basal_schedule,
            uevent=uevent
        )

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
