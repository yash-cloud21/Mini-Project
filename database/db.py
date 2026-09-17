"""
Database connection and initialisation helpers.

Usage inside Flask routes / services:
    from database.db import get_db
    db = get_db()
    rows = db.execute('SELECT ...').fetchall()
"""

import os
import sqlite3

from flask import g, current_app


def get_db():
    """Return the request-scoped database connection, creating it if needed."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row   # access columns by name
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Run schema.sql to create tables (IF NOT EXISTS — safe to re-run)."""
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        db.executescript(f.read())
    db.commit()


def init_app(app):
    """Register the close_db teardown with the Flask app."""
    app.teardown_appcontext(close_db)
