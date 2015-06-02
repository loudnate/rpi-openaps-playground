from datetime import timedelta
from flask import Flask
from flask import render_template

from glucodyn import GlucoDynEventHistory
import pump

app = Flask(__name__, static_url_path='')


@app.route("/")
def glucodyn():
    """Renders a GlucoDyn prediction graph from the current pump settings and recent history"""
    pump_datetime = pump.clock_datetime()

    # Glucodyn template data
    settings = {
        "cratio": pump.carb_ratio_at_time(pump_datetime.time()),
        "sensf": pump.insulin_sensitivity_at_time(pump_datetime.time()),
        "idur": pump.insulin_action_curve(),
        "bginitial": pump.glucose_level_at_datetime(pump_datetime),
        "stats": 1,
        "inputeffect": 1
    }

    settings["simlength"] = settings["idur"]

    history = GlucoDynEventHistory(
        pump.history_in_range(
            pump_datetime - timedelta(hours=settings["simlength"]),
            pump_datetime
        ),
        zero_datetime = pump_datetime
    )

    return render_template(
        'glucodyn.html',
        userdata=settings,
        cache_info=pump.cache_info(),
        history=history
    )

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
