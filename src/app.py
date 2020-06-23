from flask import Flask, request, url_for, redirect, Response

from src.feldman import get_latest_calendar

app = Flask(__name__)


@app.route("/MortonFeldman.ics", methods=["GET"])
def ics():
    return Response(str(get_latest_calendar()), mimetype="text/calendar")


@app.route("/")
def index():
    return redirect(url_for("ics"))


if __name__ == "__main__":
    app.run(threaded=True, port=5000)
