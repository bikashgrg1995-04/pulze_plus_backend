import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.sms_service import send_sms

from ..models import PhoneVerification, Profile, User


VERIFICATION_CODE_EXPIRY_MINUTES = 10
RESEND_COOLDOWN_SECONDS = 60


def create_phone_verification(
    user: User,
    phone_number: str,
    purpose: str,
) -> str:
    """
    Create a secure 6-digit phone verification code.

    Only the SHA-256 hash of the code is stored
    in the database. The raw code is returned so
    it can be sent through the application's SMS service.
    """

    code = f"{secrets.randbelow(1_000_000):06d}"

    code_hash = hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()

    expires_at = timezone.now() + timedelta(
        minutes=VERIFICATION_CODE_EXPIRY_MINUTES
    )

    PhoneVerification.objects.create(
        user=user,
        phone_number=phone_number,
        purpose=purpose,
        code_hash=code_hash,
        expires_at=expires_at,
    )

    return code


def send_phone_verification_sms(
    phone_number: str,
    code: str,
) -> None:
    """
    Send the phone verification OTP.

    Development mode:
    The SMS is printed to the Django console/log
    instead of being sent to a real phone.
    """

    send_sms(
        phone_number=phone_number,
        message=(
            f"Your Pulze+ verification code is {code}. "
            f"This code expires in "
            f"{VERIFICATION_CODE_EXPIRY_MINUTES} minutes."
        ),
    )


def send_phone_verification(
    user: User,
    phone_number: str,
    purpose: str,
) -> str:
    """
    Create and send a new phone verification code.

    Returns:
        The generated verification code.
    """

    code = create_phone_verification(
        user=user,
        phone_number=phone_number,
        purpose=purpose,
    )

    send_phone_verification_sms(
        phone_number=phone_number,
        code=code,
    )

    return code


def verify_phone_code(
    user: User,
    phone_number: str,
    purpose: str,
    code: str,
) -> str:
    """
    Verify a phone verification code.

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
            PhoneVerification.objects
            .select_for_update()
            .select_related("user")
            .filter(
                user=user,
                phone_number=phone_number,
                purpose=purpose,
                code_hash=code_hash,
            )
            .order_by("-created_at")
            .first()
        )

        if verification is None:
            return "invalid_or_expired"

        if verification.used_at is not None:
            return "invalid_or_expired"

        if verification.verified_at is not None:
            return "already_verified"

        if verification.expires_at <= timezone.now():
            return "invalid_or_expired"

        now = timezone.now()

        verification.verified_at = now

        verification.save(
            update_fields=["verified_at"]
        )

        if purpose == PhoneVerification.PROFILE_PHONE:
            profile = Profile.objects.select_for_update().get(
                user=user
            )

            profile.phone_number = phone_number
            profile.is_phone_verified = True

            profile.save(
                update_fields=[
                    "phone_number",
                    "is_phone_verified",
                    "updated_at",
                ]
            )

        return "verified"


def resend_phone_verification(
    user: User,
    phone_number: str,
    purpose: str,
) -> tuple[str, str]:
    """
    Create and send a new phone verification code.

    Returns:
        ("sent", code)
        ("cooldown", "")
    """

    now = timezone.now()

    latest_verification = (
        PhoneVerification.objects
        .filter(
            user=user,
            phone_number=phone_number,
            purpose=purpose,
        )
        .order_by("-created_at")
        .first()
    )

    if latest_verification is not None:
        cooldown_until = (
            latest_verification.created_at
            + timedelta(seconds=RESEND_COOLDOWN_SECONDS)
        )

        if now < cooldown_until:
            return "cooldown", ""

    # Invalidate previous unused verification codes.
    PhoneVerification.objects.filter(
        user=user,
        phone_number=phone_number,
        purpose=purpose,
        used_at__isnull=True,
    ).update(
        used_at=now,
    )

    code = create_phone_verification(
        user=user,
        phone_number=phone_number,
        purpose=purpose,
    )

    send_phone_verification_sms(
        phone_number=phone_number,
        code=code,
    )

    return "sent", code