from flask import Flask
from .db import init_db
from .auth import auth_bp
from .routes import main_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = "super-secret-change-this"

    init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app
