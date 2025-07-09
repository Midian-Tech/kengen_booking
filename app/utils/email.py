# app/utils/email.py

from flask_mail import Message
from flask import current_app
from app.extensions import mail

def send_email(subject, recipients, body, html=None):
    """
    Sends an email using Flask-Mail.
    
    :param subject: Subject of the email
    :param recipients: List of recipient email addresses
    :param body: Plain text content
    :param html: Optional HTML content
    """
    msg = Message(
        subject=subject,
        recipients=recipients,
        body=body,
        html=html
    )
    
    try:
        mail.send(msg)
        current_app.logger.info(f"Email sent to: {recipients}")
    except Exception as e:
        current_app.logger.error(f"Error sending email: {e}")
