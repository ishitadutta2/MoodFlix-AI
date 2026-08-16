"""
services/email_service.py
---------------------------------------
Email Service
MoodFlix AI

No real mail provider is configured in this environment. Rather than
silently no-op (which would make password reset / email verification
untestable and misleading), this logs the "sent" email in full,
including the actual link, so the flow is genuinely usable in dev.

To go live: set SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD in
.env and swap _mock_send() below for a real smtplib/SendGrid/SES call.
"""

import os

from utils.logger import get_logger

log = get_logger("email")


def _mock_send(to: str, subject: str, body: str):
    log.info(
        "\n"
        "──────────────────────────────────────────────\n"
        f"📧  MOCK EMAIL (no SMTP configured)\n"
        f"To:      {to}\n"
        f"Subject: {subject}\n"
        f"{body}\n"
        "──────────────────────────────────────────────"
    )
    return True


def send_email(to: str, subject: str, body: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST")

    if not smtp_host:
        return _mock_send(to, subject, body)

    try:
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = os.getenv("SMTP_FROM", "no-reply@moodflix.ai")
        msg["To"] = to

        with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", 587))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            server.send_message(msg)

        return True
    except Exception:
        log.exception(f"Failed to send email to {to}")
        return _mock_send(to, subject, body)


def send_verification_email(to: str, name: str, verify_url: str):
    return send_email(
        to,
        "Verify your MoodFlix AI account",
        f"Hi {name},\n\nConfirm your email address to finish setting up your account:\n{verify_url}\n\n"
        "This link expires in 24 hours.",
    )


def send_password_reset_email(to: str, name: str, reset_url: str):
    return send_email(
        to,
        "Reset your MoodFlix AI password",
        f"Hi {name},\n\nSomeone requested a password reset for this account. If that was you:\n{reset_url}\n\n"
        "This link expires in 30 minutes. If you didn't request this, you can ignore this email.",
    )
