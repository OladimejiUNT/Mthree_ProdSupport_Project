"""
Pytest fixtures shared across all test modules.

Database strategy:
  - A single SQLite in-memory database is created once per test session.
  - Seed data (two users, one category) is inserted once.
  - Each test receives a fresh test_client(), so session/cookie state
    does not bleed between tests.
"""
import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.category import Category


@pytest.fixture(scope='session')
def app():
    """
    Application configured for testing.

    We do NOT keep an outer app-context alive during the test run — Flask would
    reuse it for every request and g._login_user would leak between tests.
    create_app() already calls db.create_all() inside its own context; we just
    add the extra test seed data in a short-lived context here.
    StaticPool in TestingConfig ensures all those separate contexts share the
    same in-memory SQLite connection.
    """
    application = create_app('testing')
    with application.app_context():
        _seed()
    yield application
    with application.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='session')
def db(app):
    return _db


@pytest.fixture()
def client(app):
    """Unauthenticated test client — fresh cookie jar per test."""
    return app.test_client()


@pytest.fixture()
def auth_client(app):
    """Test client authenticated as a regular user via the login form."""
    c = app.test_client()
    c.post('/auth/login', data={
        'email': 'user@test.com',
        'password': 'testpassword123',
    })
    return c


@pytest.fixture()
def admin_client(app):
    """Test client authenticated as an admin user via the login form."""
    c = app.test_client()
    c.post('/auth/login', data={
        'email': 'admin@test.com',
        'password': 'adminpassword123',
    })
    return c


# ── helpers ────────────────────────────────────────────────────────────────────

def _seed():
    """Insert baseline test data (idempotent — skips if already present)."""
    if not User.query.filter_by(email='user@test.com').first():
        u = User(email='user@test.com', name='Test User', role='user')
        u.set_password('testpassword123')
        _db.session.add(u)

    if not User.query.filter_by(email='admin@test.com').first():
        a = User(email='admin@test.com', name='Test Admin', role='admin')
        a.set_password('adminpassword123')
        _db.session.add(a)

    if not Category.query.filter_by(name='Test Category').first():
        _db.session.add(Category(name='Test Category', description='Used in tests'))

    _db.session.commit()
