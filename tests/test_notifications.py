"""Tests for email notification diagnostics and CLI smoke-test command."""
from app.services import notification_service


class TestNotificationConfig:
    def test_config_status_reports_missing_smtp_fields(self, app):
        with app.app_context():
            app.config['EMAIL_ALERTS_ENABLED'] = True
            app.config['EMAIL_TRANSPORT'] = 'smtp'
            app.config['INCIDENT_ALERT_SEVERITY'] = 'critical'
            app.config['INCIDENT_ALERT_EMAIL_TO'] = 'alerts@example.com'
            app.config['SMTP_SERVER'] = ''
            app.config['SMTP_USERNAME'] = ''
            app.config['SMTP_PASSWORD'] = ''
            app.config['SMTP_FROM_EMAIL'] = ''

            status = notification_service.get_email_alert_config_status()

            assert status['enabled'] is True
            assert status['transport'] == 'smtp'
            assert status['recipient_configured'] is True
            assert 'SMTP_SERVER' in status['missing']
            assert 'SMTP_USERNAME' in status['missing']
            assert 'SMTP_PASSWORD' in status['missing']
            assert 'SMTP_FROM_EMAIL' in status['missing']

    def test_config_status_prefers_resend_in_auto_mode(self, app):
        with app.app_context():
            app.config['EMAIL_ALERTS_ENABLED'] = True
            app.config['EMAIL_TRANSPORT'] = 'auto'
            app.config['INCIDENT_ALERT_EMAIL_TO'] = 'alerts@example.com'
            app.config['RESEND_API_KEY'] = 'resend-key'
            app.config['RESEND_FROM_EMAIL'] = 'alerts@example.com'
            app.config['SMTP_SERVER'] = ''
            app.config['SMTP_USERNAME'] = ''
            app.config['SMTP_PASSWORD'] = ''
            app.config['SMTP_FROM_EMAIL'] = ''

            status = notification_service.get_email_alert_config_status()

            assert status['transport'] == 'resend'
            assert status['resend_api_key_configured'] is True
            assert status['resend_from_configured'] is True
            assert status['missing'] == []


class TestNotificationCLI:
    def test_send_test_email_cli_uses_notification_service(self, app, monkeypatch):
        with app.app_context():
            app.config['EMAIL_ALERTS_ENABLED'] = True
            app.config['INCIDENT_ALERT_EMAIL_TO'] = 'alerts@example.com'
            app.config['SMTP_SERVER'] = 'smtp.example.com'
            app.config['SMTP_USERNAME'] = 'sender@example.com'
            app.config['SMTP_PASSWORD'] = 'app-password'
            app.config['SMTP_FROM_EMAIL'] = 'sender@example.com'

            called = {'recipient': None}

            def _fake_send(recipient=None):
                called['recipient'] = recipient
                return True

            monkeypatch.setattr(
                'app.services.notification_service.send_deployment_smoke_test_email',
                _fake_send,
            )

            runner = app.test_cli_runner()
            result = runner.invoke(args=['send-test-email', '--to', 'override@example.com'])

            assert result.exit_code == 0
            assert 'Smoke-test email sent successfully.' in result.output
            assert called['recipient'] == 'override@example.com'


class TestNotificationTransports:
    def test_send_email_uses_resend_transport(self, app, monkeypatch):
        with app.app_context():
            app.config['EMAIL_ALERTS_ENABLED'] = True
            app.config['EMAIL_TRANSPORT'] = 'resend'
            app.config['INCIDENT_ALERT_EMAIL_TO'] = 'alerts@example.com'
            app.config['RESEND_API_KEY'] = 'resend-key'
            app.config['RESEND_FROM_EMAIL'] = 'alerts@example.com'

            called = {'value': False}

            class _Response:
                def raise_for_status(self):
                    return None

            def _fake_post(url, headers, json, timeout):
                called['value'] = True
                assert url.endswith('/emails')
                assert json['to'] == ['alerts@example.com']
                return _Response()

            monkeypatch.setattr('app.services.notification_service.requests.post', _fake_post)

            sent = notification_service.send_deployment_smoke_test_email()

            assert sent is True
            assert called['value'] is True