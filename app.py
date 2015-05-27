from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def glucodyn_live():
    """Renders a GlucoDyn effect graph from the current pump settings and recent history

    Note that this invokes the pump RF calls on demand. Great for debugging, but not for normal use.
    """
    import json
    from subprocess import check_output

    read_settings_dict = json.loads(check_output(["openaps", "use", "pump", "read_settings"]))

    return json.dumps(read_settings_dict)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
