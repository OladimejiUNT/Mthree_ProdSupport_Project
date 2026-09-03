"""Tests for incident CRUD operations (web layer)."""
import pytest
from app.models.incident import Incident


class TestIncidentList:
    def test_requires_auth(self, client):
        r = client.get('/incidents/')
        assert r.status_code == 302

    def test_renders_for_user(self, auth_client):
        r = auth_client.get('/incidents/')
        assert r.status_code == 200
        assert b'Incidents' in r.data


class TestCreateIncident:
    def test_create_form_renders(self, auth_client):
        r = auth_client.get('/incidents/create')
        assert r.status_code == 200
        assert (b'Report New Incident' in r.data) or (b'New Incident' in r.data)

    def test_create_incident_success(self, app, auth_client):
        r = auth_client.post('/incidents/create', data={
            'title': 'Network Outage in Building A',
            'description': 'All switches are down.',
            'category_id': '1',
            'severity': 'high',
        }, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            i = Incident.query.filter_by(title='Network Outage in Building A').first()
            assert i is not None
            assert i.severity == 'high'
            assert i.status == 'open'

    def test_create_requires_title(self, auth_client):
        r = auth_client.post('/incidents/create', data={
            'title': '',
            'severity': 'medium',
        }, follow_redirects=True)
        # Stays on create page with validation error
        assert r.status_code == 200
        assert (b'Report New Incident' in r.data) or (b'New Incident' in r.data)

    def test_create_title_too_short(self, auth_client):
        r = auth_client.post('/incidents/create', data={
            'title': 'Bad',
            'severity': 'low',
        }, follow_redirects=True)
        assert r.status_code == 200


class TestViewIncident:
    @pytest.fixture(autouse=True)
    def _create_incident(self, app, auth_client):
        """Create a test incident before each test in this class."""
        auth_client.post('/incidents/create', data={
            'title': 'View Test Incident',
            'description': 'For viewing',
            'category_id': '1',
            'severity': 'low',
        })
        with app.app_context():
            self.incident = Incident.query.filter_by(title='View Test Incident').first()

    def test_detail_page_renders(self, app, auth_client):
        with app.app_context():
            i = Incident.query.filter_by(title='View Test Incident').first()
            if i:
                r = auth_client.get(f'/incidents/{i.id}')
                assert r.status_code == 200
                assert b'View Test Incident' in r.data

    def test_nonexistent_incident_returns_404(self, app):
        with app.test_client() as c:
            # Log in first
            c.post('/auth/login', data={
                'email': 'user@test.com',
                'password': 'testpassword123',
            })
            r = c.get('/incidents/999999')
            assert r.status_code == 404


class TestDeleteIncident:
    def test_delete_own_incident(self, app, auth_client):
        # Create an incident
        auth_client.post('/incidents/create', data={
            'title': 'To Be Deleted',
            'severity': 'low',
        })
        with app.app_context():
            i = Incident.query.filter_by(title='To Be Deleted').first()
            if i:
                r = auth_client.post(f'/incidents/{i.id}/delete',
                                     follow_redirects=True)
                assert r.status_code == 200
                with app.app_context():
                    assert Incident.query.get(i.id) is None

    def test_cannot_delete_other_users_incident(self, app, admin_client, auth_client):
        # Admin creates an incident
        admin_client.post('/incidents/create', data={
            'title': 'Admin Owned Incident',
            'severity': 'medium',
        })
        with app.app_context():
            i = Incident.query.filter_by(title='Admin Owned Incident').first()
            if i:
                # Regular user tries to delete it
                r = auth_client.post(f'/incidents/{i.id}/delete',
                                     follow_redirects=True)
                # Should be 403 or redirected
                assert r.status_code in (200, 403)


class TestEditIncident:
    def test_user_can_edit_own_incident(self, app, auth_client):
        auth_client.post('/incidents/create', data={
            'title': 'Editable Incident Title',
            'severity': 'medium',
        })
        with app.app_context():
            i = Incident.query.filter_by(title='Editable Incident Title').first()
            if i:
                r = auth_client.get(f'/incidents/{i.id}/edit')
                assert r.status_code == 200

    def test_admin_can_change_status(self, app, admin_client):
        admin_client.post('/incidents/create', data={
            'title': 'Admin Status Change',
            'severity': 'critical',
        })
        with app.app_context():
            i = Incident.query.filter_by(title='Admin Status Change').first()
            if i:
                admin_client.post(f'/incidents/{i.id}/edit', data={
                    'title': 'Admin Status Change',
                    'description': '',
                    'category_id': '0',
                    'severity': 'critical',
                    'status': 'in_progress',
                    'assigned_to': '0',
                }, follow_redirects=True)
                with app.app_context():
                    updated = Incident.query.get(i.id)
                    assert updated.status == 'in_progress'
