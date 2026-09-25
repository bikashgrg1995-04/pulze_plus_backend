import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.email_service import send_email

from ..models import PasswordResetCode, PasswordResetToken, User


PASSWORD_RESET_CODE_EXPIRY_MINUTES = 10
PASSWORD_RESET_RESEND_COOLDOWN_SECONDS = 60
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 10


def create_password_reset_code(user: User) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"

    code_hash = hashlib.sha256(
        code.encode("utf-8"),
    ).hexdigest()

    expires_at = timezone.now() + timedelta(
        minutes=PASSWORD_RESET_CODE_EXPIRY_MINUTES,
    )

    PasswordResetCode.objects.create(
        user=user,
        code_hash=code_hash,
        expires_at=expires_at,
    )

    return code


def send_password_reset_email(
    user: User,
    code: str,
) -> None:
    send_email(
        to_email=user.email,
        subject="Your Pulze+ password reset code",
        html=f"""
            <h2>Reset your Pulze+ password</h2>

            <p>Hi {user.full_name},</p>

            <p>
                We received a request to reset your Pulze+
                account password.
            </p>

            <p>
                Use the verification code below:
            </p>

            <h1>{code}</h1>

            <p>
                This code will expire in
                {PASSWORD_RESET_CODE_EXPIRY_MINUTES} minutes.
            </p>

            <p>
                If you did not request a password reset,
                you can safely ignore this email.
            </p>
        """,
    )


def verify_password_reset_code(
    user: User,
    code: str,
) -> str | None:
    code_hash = hashlib.sha256(
        code.encode("utf-8"),
    ).hexdigest()

    with transaction.atomic():
        reset_code = (
            PasswordResetCode.objects
            .select_for_update()
            .filter(
                user=user,
                code_hash=code_hash,
            )
            .order_by("-created_at")
            .first()
        )

        if reset_code is None:
            return None

        if reset_code.used_at is not None:
            return None

        if reset_code.expires_at <= timezone.now():
            return None

        reset_code.used_at = timezone.now()

        reset_code.save(
            update_fields=["used_at"],
        )

    return create_password_reset_token(user)


def create_password_reset_token(user: User) -> str:
    token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        token.encode("utf-8"),
    ).hexdigest()

    expires_at = timezone.now() + timedelta(
        minutes=PASSWORD_RESET_TOKEN_EXPIRY_MINUTES,
    )

    PasswordResetToken.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(
        used_at=timezone.now(),
    )

    PasswordResetToken.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    return token


def get_valid_password_reset_token(
    token: str,
) -> PasswordResetToken | None:
    token_hash = hashlib.sha256(
        token.encode("utf-8"),
    ).hexdigest()

    reset_token = (
        PasswordResetToken.objects
        .select_related("user")
        .filter(
            token_hash=token_hash,
            used_at__isnull=True,
        )
        .first()
    )

    if reset_token is None:
        return None

    if reset_token.expires_at <= timezone.now():
        return None

    return reset_token


def resend_password_reset_code(user: User) -> str:
    now = timezone.now()

    latest_code = (
        PasswordResetCode.objects
        .filter(user=user)
        .order_by("-created_at")
        .first()
    )

    if latest_code is not None:
        cooldown_until = (
            latest_code.created_at
            + timedelta(
                seconds=PASSWORD_RESET_RESEND_COOLDOWN_SECONDS,
            )
        )

        if now < cooldown_until:
            return "cooldown"

    PasswordResetCode.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(
        used_at=now,
    )

    code = create_password_reset_code(user)

    send_password_reset_email(
        user=user,
        code=code,
    )

    return "sent"