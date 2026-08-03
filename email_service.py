import smtplib
from email.mime.text import MIMEText

from config import GMAIL_APP_PASSWORD, GMAIL_USER


def email_configured() -> bool:
    return bool(GMAIL_USER and GMAIL_APP_PASSWORD)


def send_email(subject, body):
    if not email_configured():
        raise RuntimeError(
            "Email is not configured. Add GMAIL_USER and GMAIL_APP_PASSWORD in .env "
            "(Google Account -> Security -> 2-Step Verification -> App passwords)."
        )
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
    return GMAIL_USER
