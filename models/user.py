"""
User model for Flask-Login integration.

This is *not* an ORM model — we use raw SQL with sqlite3.Row for
simplicity.  The class wraps a database row and satisfies the
Flask-Login UserMixin interface.
"""

import sqlite3

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db


class User(UserMixin):
    """Lightweight user object backed by the `users` table."""

    def __init__(self, id, username, email, password_hash, role, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_user(row):
        """Convert a sqlite3.Row to a User instance (or None)."""
        if row is None:
            return None
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=row['role'],
            created_at=row['created_at'],
        )

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return User._row_to_user(row)

    @staticmethod
    def get_by_username(username):
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        return User._row_to_user(row)

    @staticmethod
    def get_by_email(email):
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        return User._row_to_user(row)

    # ------------------------------------------------------------------
    # Mutating helpers
    # ------------------------------------------------------------------

    @staticmethod
    def create(username, email, password, role='student'):
        """Insert a new user.  Returns the User on success, None on duplicate."""
        db = get_db()
        pw_hash = generate_password_hash(password)
        try:
            db.execute(
                'INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
                (username, email, pw_hash, role),
            )
            db.commit()
            return User.get_by_username(username)
        except sqlite3.IntegrityError:
            return None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ------------------------------------------------------------------
    # Role helpers
    # ------------------------------------------------------------------

    @property
    def is_admin(self):
        return self.role == 'admin'
