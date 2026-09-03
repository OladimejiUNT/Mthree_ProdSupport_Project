"""Notification service for operational alerts."""
import smtplib
from email.message import EmailMessage
from types import SimpleNamespace
from flask import current_app


def get_email_alert_config_status() -> dict:
    """Return a safe summary of email alert configuration."""
    cfg = current_app.config
    recipient = (cfg.get('INCIDENT_ALERT_EMAIL_TO') or '').strip()
    smtp_server = (cfg.get('SMTP_SERVER') or '').strip()
    smtp_username = (cfg.get('SMTP_USERNAME') or '').strip()
    smtp_password = cfg.get('SMTP_PASSWORD') or ''
    from_email = (cfg.get('SMTP_FROM_EMAIL') or '').strip()

    missing = [
        key for key, value in {
            'INCIDENT_ALERT_EMAIL_TO': recipient,
            'SMTP_SERVER': smtp_server,
            'SMTP_USERNAME': smtp_username,
            'SMTP_PASSWORD': smtp_password,
            'SMTP_FROM_EMAIL': from_email,
        }.items() if not str(value).strip()
    ]

    return {
        'enabled': bool(cfg.get('EMAIL_ALERTS_ENABLED', False)),
        'trigger_severity': str(cfg.get('INCIDENT_ALERT_SEVERITY', 'critical')).lower(),
        'recipient_configured': bool(recipient),
        'smtp_server_configured': bool(smtp_server),
        'smtp_username_configured': bool(smtp_username),
        'smtp_password_configured': bool(str(smtp_password).strip()),
        'smtp_from_configured': bool(from_email),
        'missing': missing,
    }


def log_email_alert_configuration() -> None:
    """Log a safe summary of email alert readiness without exposing secrets."""
    status = get_email_alert_config_status()
    current_app.logger.info(
        'Email alerts status: enabled=%s trigger_severity=%s recipient_configured=%s '
        'smtp_server_configured=%s smtp_username_configured=%s smtp_password_configured=%s '
        'smtp_from_configured=%s missing=%s',
        status['enabled'],
        status['trigger_severity'],
        status['recipient_configured'],
        status['smtp_server_configured'],
        status['smtp_username_configured'],
        status['smtp_password_configured'],
        status['smtp_from_configured'],
        ','.join(status['missing']) or 'none',
    )


def _send_email(subject: str, body: str, recipient: str = None) -> bool:
    """Send an email using configured SMTP credentials."""
    cfg = current_app.config

    if not cfg.get('EMAIL_ALERTS_ENABLED', False):
        return False

    recipient = (recipient or cfg.get('INCIDENT_ALERT_EMAIL_TO') or '').strip()
    smtp_server = (cfg.get('SMTP_SERVER') or '').strip()
    smtp_username = (cfg.get('SMTP_USERNAME') or '').strip()
    smtp_password = cfg.get('SMTP_PASSWORD') or ''
    from_email = (cfg.get('SMTP_FROM_EMAIL') or '').strip()
    smtp_port = int(cfg.get('SMTP_PORT', 587))
    use_tls = bool(cfg.get('SMTP_USE_TLS', True))

    if not recipient or not smtp_server or not smtp_username or not smtp_password or not from_email:
        current_app.logger.warning(
            'Critical incident email not sent: missing SMTP or recipient configuration.'
        )
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = recipient
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(smtp_username, smtp_password)
            smtp.send_message(msg)
        return True
    except Exception:
        current_app.logger.exception('Failed to send critical incident email alert.')
        return False


def send_critical_incident_email(incident, reporter_name: str) -> bool:
    """Send a critical incident alert email.

    Returns True when an email was attempted successfully, otherwise False.
    """
    subject = f"[CRITICAL] Incident #{incident.id}: {incident.title}"
    body = (
        'A critical incident has been recorded in IT Support Portal.\n\n'
        f"Incident ID: {incident.id}\n"
        f"Title: {incident.title}\n"
        f"Severity: {incident.severity}\n"
        f"Status: {incident.status}\n"
        f"Category: {incident.category.name if incident.category else 'Uncategorized'}\n"
        f"Reported By: {reporter_name}\n"
        f"Description: {incident.description or 'N/A'}\n"
    )
    return _send_email(subject, body)


def send_deployment_smoke_test_email(recipient: str = None) -> bool:
    """Send a deployment smoke-test email using current SMTP configuration."""
    incident = SimpleNamespace(
        id='smoke-test',
        title='Deployment Email Smoke Test',
        severity='critical',
        status='open',
        category=None,
        description='This is a deployment smoke test triggered from the Flask CLI.',
    )
    body = (
        'This is a deployment smoke test for IT Support Portal email alerts.\n\n'
        f"Incident ID: {incident.id}\n"
        f"Title: {incident.title}\n"
        f"Severity: {incident.severity}\n"
        f"Status: {incident.status}\n"
        f"Description: {incident.description}\n"
    )
    return _send_email('[TEST] IT Support Portal email alert', body, recipient=recipient)
