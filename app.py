"""
Student Career & Skill Development Platform
============================================
Main Flask application factory.

Run:
    python app.py

Default admin account (created on first launch):
    username: admin
    password: admin123
"""

import os

from flask import Flask
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash

from config import Config
from database.db import get_db, init_db, init_app as init_db_app
from models.user import User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Extensions ---
    CSRFProtect(app)                       # Global CSRF protection

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    # Load SECRET_KEY from environment variables for deployment, fallback to default for local
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')

    # --- Database ---
    init_db_app(app)

    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        init_db()
        _seed_admin()
        _seed_coding_problems()

    # --- Blueprints ---
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.academics import academics_bp
    from routes.coding import coding_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(academics_bp)      # url_prefix set inside the blueprint
    app.register_blueprint(coding_bp)         # url_prefix='/coding'

    return app


def _seed_admin():
    """Create a default admin account if no admin exists yet."""
    db = get_db()
    admin = db.execute("SELECT 1 FROM users WHERE role = 'admin'").fetchone()
    if admin is None:
        pw_hash = generate_password_hash('admin123')
        db.execute(
            'INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
            ('admin', 'admin@platform.com', pw_hash, 'admin'),
        )
        db.commit()
        print('  [OK] Default admin account created  (admin / admin123)')


def _seed_coding_problems():
    """Seed the initial set of coding problems if the table is empty."""
    from services.coding_service import seed_problems
    seed_problems()


# ------------------------------------------------------------------

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
