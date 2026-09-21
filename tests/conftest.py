import os
import tempfile
import pytest
from app import create_app
from database.db import init_db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_path = tempfile.mkstemp()

    # Override config for testing
    class TestConfig:
        TESTING = True
        SECRET_KEY = 'test-key'
        DATABASE = db_path
        WTF_CSRF_ENABLED = False # Disable CSRF for easier form testing
        UPLOAD_FOLDER = tempfile.mkdtemp() # Add temporary upload folder

    app = create_app(TestConfig)

    # Initialize the test database
    with app.app_context():
        init_db()

    yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's click commands."""
    return app.test_cli_runner()
