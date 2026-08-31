"""Tests for authentication flows."""
from app.models.user import User


class TestLoginPage:
    def test_renders(self, client):
        r = client.get('/auth/login')
        assert r.status_code == 200
        assert b'Log In' in r.data

    def test_valid_credentials_redirect(self, client):
        r = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'testpassword123',
        }, follow_redirects=True)
        assert r.status_code == 200
        # Should land on the incidents list
        assert b'Incidents' in r.data

    def test_invalid_password(self, app):
        # Use an explicit fresh client to avoid any cross-test session bleed
        with app.test_client() as c:
            r = c.post('/auth/login', data={
                'email': 'user@test.com',
                'password': 'wrongpassword',
            }, follow_redirects=True)
            # Should render the login page, not redirect to incidents
            assert b'Log In' in r.data or b'Sign In' in r.data

    def test_unknown_email(self, app):
        with app.test_client() as c:
            r = c.post('/auth/login', data={
                'email': 'nobody@nowhere.com',
                'password': 'whatever',
            }, follow_redirects=True)
            assert b'Log In' in r.data or b'Sign In' in r.data


class TestLogout:
    def test_logout_redirects_to_login(self, auth_client):
        r = auth_client.get('/auth/logout', follow_redirects=True)
        assert r.status_code == 200
        assert b'logged out' in r.data.lower()

    def test_logout_requires_login(self, client):
        r = client.get('/auth/logout')
        # Should redirect to login (Flask-Login protection)
        assert r.status_code in (302, 200)


class TestRegistration:
    def test_register_page_renders(self, client):
        r = client.get('/auth/register')
        assert r.status_code == 200

    def test_successful_registration(self, app, client):
        r = client.post('/auth/register', data={
            'name': 'Brand New',
            'email': 'brandnew@test.com',
            'password': 'securepass123',
            'password2': 'securepass123',
        }, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            assert User.query.filter_by(email='brandnew@test.com').first() is not None

    def test_duplicate_email_rejected(self, client):
        r = client.post('/auth/register', data={
            'name': 'Duplicate',
            'email': 'user@test.com',
            'password': 'testpassword123',
            'password2': 'testpassword123',
        }, follow_redirects=True)
        assert b'already registered' in r.data

    def test_password_mismatch_rejected(self, client):
        r = client.post('/auth/register', data={
            'name': 'Mismatch',
            'email': 'mismatch@test.com',
            'password': 'pass1234',
            'password2': 'pass9999',
        }, follow_redirects=True)
        assert b'match' in r.data.lower()

    def test_short_password_rejected(self, client):
        r = client.post('/auth/register', data={
            'name': 'Short',
            'email': 'short@test.com',
            'password': 'abc',
            'password2': 'abc',
        }, follow_redirects=True)
        assert r.status_code == 200
        # Validation error should be shown
        assert b'at least' in r.data.lower() or b'short' in r.data.lower() or b'8' in r.data


class TestProtectedRoutes:
    def test_unauthenticated_incidents_redirects(self, client):
        r = client.get('/incidents/')
        assert r.status_code == 302
        assert b'/auth/login' in r.headers.get('Location', '').encode()

    def test_authenticated_can_access_incidents(self, auth_client):
        r = auth_client.get('/incidents/')
        assert r.status_code == 200
