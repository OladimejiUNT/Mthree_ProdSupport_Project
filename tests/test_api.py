"""Tests for the JSON REST API (/api/*)."""
import json


def _json(r):
    return json.loads(r.data)


class TestIncidentsAPI:
    def test_requires_auth(self, client):
        r = client.get('/api/incidents')
        # Flask-Login redirects to login page
        assert r.status_code in (302, 401)

    def test_list_incidents_returns_list(self, auth_client):
        r = auth_client.get('/api/incidents')
        assert r.status_code == 200
        body = _json(r)
        assert 'data' in body
        assert isinstance(body['data'], list)

    def test_create_incident(self, auth_client):
        r = auth_client.post(
            '/api/incidents',
            data=json.dumps({'title': 'API Created Incident', 'severity': 'high',
                             'description': 'Via REST API'}),
            content_type='application/json',
        )
        assert r.status_code == 201
        body = _json(r)
        assert body['data']['title'] == 'API Created Incident'
        assert body['data']['severity'] == 'high'
        assert body['data']['status'] == 'open'

    def test_create_incident_missing_title(self, auth_client):
        r = auth_client.post(
            '/api/incidents',
            data=json.dumps({'severity': 'low'}),
            content_type='application/json',
        )
        assert r.status_code == 400
        assert 'error' in _json(r)

    def test_get_single_incident(self, auth_client):
        # Create first
        create_r = auth_client.post(
            '/api/incidents',
            data=json.dumps({'title': 'Get Single Test', 'severity': 'low'}),
            content_type='application/json',
        )
        incident_id = _json(create_r)['data']['id']

        r = auth_client.get(f'/api/incidents/{incident_id}')
        assert r.status_code == 200
        assert _json(r)['data']['id'] == incident_id

    def test_get_nonexistent_incident_404(self, auth_client):
        r = auth_client.get('/api/incidents/999999')
        assert r.status_code == 404

    def test_update_incident(self, auth_client):
        create_r = auth_client.post(
            '/api/incidents',
            data=json.dumps({'title': 'Update Me', 'severity': 'low'}),
            content_type='application/json',
        )
        incident_id = _json(create_r)['data']['id']

        r = auth_client.put(
            f'/api/incidents/{incident_id}',
            data=json.dumps({'title': 'Updated Title', 'severity': 'high'}),
            content_type='application/json',
        )
        assert r.status_code == 200
        assert _json(r)['data']['title'] == 'Updated Title'

    def test_delete_incident(self, auth_client):
        create_r = auth_client.post(
            '/api/incidents',
            data=json.dumps({'title': 'Delete Me', 'severity': 'low'}),
            content_type='application/json',
        )
        incident_id = _json(create_r)['data']['id']

        r = auth_client.delete(f'/api/incidents/{incident_id}')
        assert r.status_code == 200
        assert 'deleted' in _json(r).get('message', '').lower()

        # Confirm gone
        r2 = auth_client.get(f'/api/incidents/{incident_id}')
        assert r2.status_code == 404

    def test_filter_by_status(self, auth_client):
        r = auth_client.get('/api/incidents?status=open')
        assert r.status_code == 200
        for item in _json(r)['data']:
            assert item['status'] == 'open'


class TestStatsAPI:
    def test_stats_shape(self, auth_client):
        r = auth_client.get('/api/stats')
        assert r.status_code == 200
        data = _json(r)['data']
        for key in ('total', 'open', 'in_progress', 'resolved', 'closed'):
            assert key in data
            assert isinstance(data[key], int)


class TestCategoriesAPI:
    def test_categories_returns_list(self, auth_client):
        r = auth_client.get('/api/categories')
        assert r.status_code == 200
        body = _json(r)
        assert 'data' in body
        assert isinstance(body['data'], list)
        # Seeded categories should be present
        assert len(body['data']) > 0
