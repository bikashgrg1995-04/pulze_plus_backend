import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger(__name__)


class EmailServiceUnavailable(APIException):
    """
    Raised when the email provider is unavailable
    or an email cannot be sent.
    """

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    default_detail = (
        "We couldn't send the verification email. "
        "Please try again later."
    )

    default_code = "email_service_unavailable"


def custom_exception_handler(exc, context):
    """
    Return a consistent API error response.
    """

    response = exception_handler(exc, context)

    if response is not None:
        data = response.data

        if isinstance(data, dict) and "detail" in data:
            message = data["detail"]
            errors = {}
        elif isinstance(data, dict):
            message = "Please correct the errors below."
            errors = data
        else:
            message = "An error occurred."
            errors = {}

        response.data = {
            "message": message,
            "errors": errors,
        }

        return response

    # Unexpected server-side exception.
    request = context.get("request")

    logger.exception(
        "Unhandled API exception",
        extra={
            "method": getattr(request, "method", None),
            "path": getattr(request, "path", None),
        },
    )

    return Response(
        {
            "message": "Something went wrong. Please try again later.",
            "errors": {},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )