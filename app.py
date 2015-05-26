from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    from subprocess import check_output

    return check_output(["openaps", "use", "pump", "read_settings"])

if __name__ == "__main__":
    app.run(host='0.0.0.0')
