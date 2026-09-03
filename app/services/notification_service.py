"""Notification service for operational alerts."""
import smtplib
from email.message import EmailMessage
from types import SimpleNamespace
from flask import current_app
import requests


def _resolve_transport() -> str:
    """Resolve the configured email transport."""
    cfg = current_app.config
    configured = str(cfg.get('EMAIL_TRANSPORT', 'auto')).lower()
    resend_key = (cfg.get('RESEND_API_KEY') or '').strip()
    resend_from = (cfg.get('RESEND_FROM_EMAIL') or '').strip()
    smtp_server = (cfg.get('SMTP_SERVER') or '').strip()
    smtp_username = (cfg.get('SMTP_USERNAME') or '').strip()
    smtp_password = cfg.get('SMTP_PASSWORD') or ''
    smtp_from = (cfg.get('SMTP_FROM_EMAIL') or '').strip()

    if configured != 'auto':
        return configured
    if resend_key and resend_from:
        return 'resend'
    if smtp_server and smtp_username and smtp_password and smtp_from:
        return 'smtp'
    return 'unconfigured'


def get_email_alert_config_status() -> dict:
    """Return a safe summary of email alert configuration."""
    cfg = current_app.config
    transport = _resolve_transport()
    recipient = (cfg.get('INCIDENT_ALERT_EMAIL_TO') or '').strip()
    smtp_server = (cfg.get('SMTP_SERVER') or '').strip()
    smtp_username = (cfg.get('SMTP_USERNAME') or '').strip()
    smtp_password = cfg.get('SMTP_PASSWORD') or ''
    from_email = (cfg.get('SMTP_FROM_EMAIL') or '').strip()
    resend_api_key = (cfg.get('RESEND_API_KEY') or '').strip()
    resend_from_email = (cfg.get('RESEND_FROM_EMAIL') or '').strip()

    required = {'INCIDENT_ALERT_EMAIL_TO': recipient}
    if transport == 'resend':
        required.update({
            'RESEND_API_KEY': resend_api_key,
            'RESEND_FROM_EMAIL': resend_from_email,
        })
    elif transport == 'smtp':
        required.update({
            'SMTP_SERVER': smtp_server,
            'SMTP_USERNAME': smtp_username,
            'SMTP_PASSWORD': smtp_password,
            'SMTP_FROM_EMAIL': from_email,
        })
    else:
        required.update({
            'RESEND_API_KEY': resend_api_key,
            'RESEND_FROM_EMAIL': resend_from_email,
            'SMTP_SERVER': smtp_server,
            'SMTP_USERNAME': smtp_username,
            'SMTP_PASSWORD': smtp_password,
            'SMTP_FROM_EMAIL': from_email,
        })

    missing = [key for key, value in required.items() if not str(value).strip()]

    return {
        'enabled': bool(cfg.get('EMAIL_ALERTS_ENABLED', False)),
        'transport': transport,
        'trigger_severity': str(cfg.get('INCIDENT_ALERT_SEVERITY', 'critical')).lower(),
        'recipient_configured': bool(recipient),
        'smtp_server_configured': bool(smtp_server),
        'smtp_username_configured': bool(smtp_username),
        'smtp_password_configured': bool(str(smtp_password).strip()),
        'smtp_from_configured': bool(from_email),
        'resend_api_key_configured': bool(resend_api_key),
        'resend_from_configured': bool(resend_from_email),
        'missing': missing,
    }


def log_email_alert_configuration() -> None:
    """Log a safe summary of email alert readiness without exposing secrets."""
    status = get_email_alert_config_status()
    current_app.logger.info(
        'Email alerts status: enabled=%s transport=%s trigger_severity=%s recipient_configured=%s '
        'smtp_server_configured=%s smtp_username_configured=%s smtp_password_configured=%s '
        'smtp_from_configured=%s resend_api_key_configured=%s resend_from_configured=%s missing=%s',
        status['enabled'],
        status['transport'],
        status['trigger_severity'],
        status['recipient_configured'],
        status['smtp_server_configured'],
        status['smtp_username_configured'],
        status['smtp_password_configured'],
        status['smtp_from_configured'],
        status['resend_api_key_configured'],
        status['resend_from_configured'],
        ','.join(status['missing']) or 'none',
    )


def _send_via_resend(subject: str, body: str, recipient: str) -> bool:
    """Send an email via the Resend HTTP API."""
    cfg = current_app.config
    api_key = (cfg.get('RESEND_API_KEY') or '').strip()
    from_email = (cfg.get('RESEND_FROM_EMAIL') or '').strip()
    api_base = str(cfg.get('RESEND_API_BASE', 'https://api.resend.com')).rstrip('/')

    if not api_key or not from_email or not recipient:
        current_app.logger.warning(
            'Critical incident email not sent: missing Resend configuration.'
        )
        return False

    try:
        response = requests.post(
            f'{api_base}/emails',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'from': from_email,
                'to': [recipient],
                'subject': subject,
                'text': body,
            },
            timeout=15,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        current_app.logger.exception('Failed to send critical incident email alert via Resend.')
        return False


def _send_via_smtp(subject: str, body: str, recipient: str) -> bool:
    """Send an email using configured SMTP credentials."""
    cfg = current_app.config

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


def _send_email(subject: str, body: str, recipient: str = None) -> bool:
    """Send an email using the configured transport."""
    cfg = current_app.config

    if not cfg.get('EMAIL_ALERTS_ENABLED', False):
        return False

    recipient = (recipient or cfg.get('INCIDENT_ALERT_EMAIL_TO') or '').strip()
    transport = _resolve_transport()

    if transport == 'resend':
        return _send_via_resend(subject, body, recipient)
    if transport == 'smtp':
        return _send_via_smtp(subject, body, recipient)

    current_app.logger.warning(
        'Critical incident email not sent: no supported email transport is fully configured.'
    )
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
