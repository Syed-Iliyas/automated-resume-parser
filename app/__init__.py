"""Flask application factory."""

import os

from flask import Flask

from .config import config_by_name
from .extensions import db
from .routes.api import api


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.getenv("FLASK_CONFIG", "default")
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(api)

    return app
