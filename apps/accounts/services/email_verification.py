import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.email_service import send_email

from ..models import EmailVerification, User


VERIFICATION_TOKEN_EXPIRY_MINUTES = 30


def create_email_verification(user: User) -> str:
    """
    Create a secure email verification token.

    Only the SHA-256 hash of the token is stored
    in the database. The raw token is returned so
    it can be included in the verification email.
    """

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    expires_at = timezone.now() + timedelta(
        minutes=VERIFICATION_TOKEN_EXPIRY_MINUTES
    )

    EmailVerification.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    return raw_token


def send_verification_email(
    user: User,
    raw_token: str,
) -> None:
    """
    Send the email verification link through
    the application's email service.
    """

    verification_url = (
        "http://127.0.0.1:8000/api/v1/auth/verify-email/"
        f"?token={raw_token}"
    )

    send_email(
        to_email=user.email,
        subject="Verify your Pulze+ email",
        html=f"""
            <h2>Welcome to Pulze+</h2>

            <p>Hi {user.full_name},</p>

            <p>
                Thanks for creating your Pulze+ account.
                Please verify your email address by clicking
                the button below.
            </p>

            <p>
                <a href="{verification_url}">
                    Verify Email
                </a>
            </p>

            <p>
                This verification link will expire in
                {VERIFICATION_TOKEN_EXPIRY_MINUTES} minutes.
            </p>

            <p>
                If you did not create a Pulze+ account,
                you can safely ignore this email.
            </p>
        """,
    )


def verify_email_token(raw_token: str) -> str:
    """
    Verify an email verification token.

    Returns a result message describing the verification state.
    """

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    with transaction.atomic():
        verification = (
            EmailVerification.objects
            .select_for_update()
            .select_related("user")
            .filter(token_hash=token_hash)
            .first()
        )

        if verification is None:
            return "invalid_or_expired"

        if verification.used_at is not None:
            return "invalid_or_expired"

        if verification.expires_at <= timezone.now():
            return "invalid_or_expired"

        user = verification.user

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




RESEND_COOLDOWN_SECONDS = 60

def resend_verification_email(user: User) -> str:
    """
    Create and send a new email verification token.

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

    # Invalidate previous unused verification tokens.
    EmailVerification.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(
        used_at=now,
    )

    raw_token = create_email_verification(user)

    send_verification_email(
        user=user,
        raw_token=raw_token,
    )

    return "sent"