import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.email_service import send_email

from ..models import EmailVerification, User


VERIFICATION_CODE_EXPIRY_MINUTES = 10
RESEND_COOLDOWN_SECONDS = 60


def create_email_verification(user: User) -> str:
    """
    Create a secure 6-digit email verification code.

    Only the SHA-256 hash of the code is stored
    in the database. The raw code is returned so
    it can be included in the verification email.
    """

    code = f"{secrets.randbelow(1_000_000):06d}"

    code_hash = hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()

    expires_at = timezone.now() + timedelta(
        minutes=VERIFICATION_CODE_EXPIRY_MINUTES
    )

    EmailVerification.objects.create(
        user=user,
        code_hash=code_hash,
        expires_at=expires_at,
    )

    return code


def send_verification_email(
    user: User,
    code: str,
) -> None:
    """
    Send the email verification code through
    the application's email service.
    """

    send_email(
        to_email=user.email,
        subject="Your Pulze+ verification code",
        html=f"""
            <h2>Verify your Pulze+ email</h2>

            <p>Hi {user.full_name},</p>

            <p>
                Thanks for creating your Pulze+ account.
                Use the verification code below to verify
                your email address.
            </p>

            <h1>{code}</h1>

            <p>
                This code will expire in
                {VERIFICATION_CODE_EXPIRY_MINUTES} minutes.
            </p>

            <p>
                If you did not create a Pulze+ account,
                you can safely ignore this email.
            </p>
        """,
    )


def verify_email_code(
    user: User,
    code: str,
) -> str:
    """
    Verify an email verification code.

    Returns:
        "verified"
        "already_verified"
        "invalid_or_expired"
    """

    code_hash = hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()

    with transaction.atomic():
        verification = (
            EmailVerification.objects
            .select_for_update()
            .select_related("user")
            .filter(
                user=user,
                code_hash=code_hash,
            )
            .order_by("-created_at")
            .first()
        )

        if verification is None:
            return "invalid_or_expired"

        if verification.used_at is not None:
            return "invalid_or_expired"

        if verification.expires_at <= timezone.now():
            return "invalid_or_expired"

        if user.is_email_verified:
            return "already_verified"

        user.is_email_verified = True
        user.save(
            update_fields=[
                "is_email_verified",
                "updated_at",
            ]
        )

        verification.used_at = timezone.now()
        verification.save(
            update_fields=["used_at"]
        )

    return "verified"


def resend_verification_email(user: User) -> str:
    """
    Create and send a new email verification code.

    Returns:
        "already_verified"
        "cooldown"
        "sent"
    """

    if user.is_email_verified:
        return "already_verified"

    now = timezone.now()

    latest_verification = (
        EmailVerification.objects
        .filter(user=user)
        .order_by("-created_at")
        .first()
    )

    if latest_verification is not None:
        cooldown_until = (
            latest_verification.created_at
            + timedelta(seconds=RESEND_COOLDOWN_SECONDS)
        )

        if now < cooldown_until:
            return "cooldown"

    # Invalidate previous unused verification codes.
    EmailVerification.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(
        used_at=now,
    )

    code = create_email_verification(user)

    send_verification_email(
        user=user,
        code=code,
    )

    return "sent"