import os

from flask import Flask, request, url_for, redirect, Response
from flask_caching import Cache

from src.feldman import get_latest_calendar

CACHE_TIME = 3600 * 6
cache = Cache()


def create_app():
    app = Flask(__name__)
    cache_servers = os.environ.get("MEMCACHIER_SERVERS")
    if cache_servers == None:
        cache.init_app(app, config={"CACHE_TYPE": "simple"})
    else:
        cache_user = os.environ.get("MEMCACHIER_USERNAME") or ""
        cache_pass = os.environ.get("MEMCACHIER_PASSWORD") or ""
        cache.init_app(
            app,
            config={
                "CACHE_KEY_PREFIX": "v7",
                "CACHE_TYPE": "saslmemcached",
                "CACHE_MEMCACHED_SERVERS": cache_servers.split(","),
                "CACHE_MEMCACHED_USERNAME": cache_user,
                "CACHE_MEMCACHED_PASSWORD": cache_pass,
                "CACHE_OPTIONS": {
                    "behaviors": {
                        # Faster IO
                        "tcp_nodelay": True,
                        # Keep connection alive
                        "tcp_keepalive": True,
                        # Timeout for set/get requests
                        "connect_timeout": 2000,  # ms
                        "send_timeout": 750 * 1000,  # us
                        "receive_timeout": 750 * 1000,  # us
                        "_poll_timeout": 2000,  # ms
                        # Better failover
                        "ketama": True,
                        "remove_failed": 1,
                        "retry_timeout": 2,
                        "dead_timeout": 30,
                    }
                },
            },
        )

    return app


app = create_app()


@app.route("/MortonFeldman.ics", methods=["GET"])
@cache.cached(timeout=CACHE_TIME)
def ics():
    return Response(get_latest_calendar().to_ical().decode('utf-8'), mimetype="text/calendar")


@app.route("/")
def index():
    return redirect(url_for("ics"))


if __name__ == "__main__":
    app.run(threaded=True, port=5000)
