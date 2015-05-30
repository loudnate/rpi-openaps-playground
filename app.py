from flask import Flask
from flask import render_template

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

    return render_template(
        'glucodyn.html',
        userdata=settings,
        cache_info=pump.cache_info()
    )

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
