from flask import Flask

app = Flask(__name__)


@app.route("/")
def glucodyn():
    """Renders a GlucoDyn prediction graph from the current pump settings and recent history"""
    import pump
    import json

    pump_datetime = pump.clock_datetime()

    # Glucodyn template data
    settings = {
        "cratio": pump.carb_ratio_at_time(pump_datetime.time()),
        "sensf": pump.insulin_sensitivity_at_time(pump_datetime.time()),
        "idur": pump.insulin_action_curve(),
        "bginitial": pump.glucose_level_at_pump_datetime(pump_datetime),
        "stats": 1,
        "inputeffect": 1
    }

    settings["simlength"] = settings["idur"]

    return json.dumps(settings)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
