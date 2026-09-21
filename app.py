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

from flask import Flask, render_template
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

    # Load SECRET_KEY from config which now guarantees a secure key
    app.config['SECRET_KEY'] = config_class.SECRET_KEY

    # --- Database ---
    init_db_app(app)

    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        init_db()
        _seed_admin()
        _seed_coding_problems()
        _seed_job_roles()

    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.academics import academics_bp
    from routes.coding import coding_bp
    from routes.resume import resume_bp
    from routes.career import career_bp
    from routes.ai import ai_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(academics_bp)      # url_prefix set inside the blueprint
    app.register_blueprint(coding_bp)         # url_prefix='/coding'
    app.register_blueprint(resume_bp)
    app.register_blueprint(career_bp)
    app.register_blueprint(ai_bp)

    # --- Error Handlers ---
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

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


def _seed_job_roles():
    """Seed the predefined job roles if the table is empty."""
    from services.career_service import seed_job_roles
    seed_job_roles()


# ------------------------------------------------------------------

if __name__ == '__main__':
    app = create_app()
    # Security: debug=False for production/demo builds to prevent RCE through Werkzeug debugger
    app.run(debug=False, port=5000)
