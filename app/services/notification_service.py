"""Notification service for operational alerts."""
import smtplib
from email.message import EmailMessage
from flask import current_app


def send_critical_incident_email(incident, reporter_name: str) -> bool:
    """Send a critical incident alert email.

    Returns True when an email was attempted successfully, otherwise False.
    """
    cfg = current_app.config

    if not cfg.get('EMAIL_ALERTS_ENABLED', False):
        return False

    recipient = (cfg.get('INCIDENT_ALERT_EMAIL_TO') or '').strip()
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
