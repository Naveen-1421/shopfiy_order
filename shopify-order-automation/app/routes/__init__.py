from flask import Flask
from app.config import Config
from app.extensions import db, migrate


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize PostgreSQL
    db.init_app(app)

    # Initialize Flask-Migrate
    migrate.init_app(app, db)

    # Load models
    with app.app_context():
        from app import models

    return app