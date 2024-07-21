# utils.py
import logging
import resend
from django.conf import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY

def send_email(subject, recipient, message):
    try:
        logger.info(f"Sending email to {recipient}")
        response = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": recipient,
            "subject": subject,
            "html": message
        })
        logger.info(f"Email sent to {recipient} with response: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        return None
