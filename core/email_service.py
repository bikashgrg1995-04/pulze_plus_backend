import logging

import resend

from django.conf import settings

from core.exceptions import EmailServiceUnavailable


logger = logging.getLogger(__name__)


def send_email(
    to_email: str,
    subject: str,
    html: str,
):
    """
    Send an email through Resend.

    Resend-related failures are converted into a
    controlled application exception.
    """

    resend.api_key = settings.RESEND_API_KEY

    try:
        response = resend.Emails.send(
            {
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
        )

        return response

    except Exception as exc:
        logger.exception(
            "Failed to send email through Resend."
        )

        raise EmailServiceUnavailable() from exc