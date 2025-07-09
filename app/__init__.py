# app/__init__.py
from flask import Flask, redirect, url_for
from config import Config
from app.extensions import db, login_manager, mail  # ⬅️ include mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)  # ⬅️ initialize Flask-Mail

    from app.routes import auth, admin, staff, booking
    from app.routes.equipment import equipment as equipment_bp

    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(staff.bp)
    app.register_blueprint(booking.bp)
    app.register_blueprint(equipment_bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app
