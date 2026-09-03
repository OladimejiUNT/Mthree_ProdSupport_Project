"""Tests for admin-only views and actions."""


class TestAdminDashboard:
    def test_dashboard_renders_email_alert_status(self, admin_client):
        response = admin_client.get('/admin/dashboard')

        assert response.status_code == 200
        assert b'Email Alerts' in response.data
        assert b'Send Test Email' in response.data


class TestAdminEmailActions:
    def test_send_test_email_route_invokes_notification_service(self, admin_client, monkeypatch):
        called = {'value': False}

        def _fake_send(recipient=None):
            called['value'] = True
            return True

        monkeypatch.setattr(
            'app.services.notification_service.send_deployment_smoke_test_email',
            _fake_send,
        )

        response = admin_client.post('/admin/send-test-email', follow_redirects=True)

        assert response.status_code == 200
        assert called['value'] is True
        assert b'Test email sent successfully.' in response.data
