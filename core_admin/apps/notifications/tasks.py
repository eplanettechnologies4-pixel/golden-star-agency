import logging
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def send_notification_email(recipient_email, subject, body):
    """
    Sample Celery task for sending notification emails.
    """
    logger.info(f"Sending email to {recipient_email} with subject: '{subject}'")
    # Simulate sending email
    return True
