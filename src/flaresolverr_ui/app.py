"""Minimal Flask app for FlareSolverr status/test UI."""
from flask import Flask


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY="dev")
    if config:
        app.config.from_mapping(config)

    @app.route("/")
    def index():
        return "<h1>FlareSolverr UI</h1><p>Status and URL test. Configure routes as needed.</p>"

    return app
