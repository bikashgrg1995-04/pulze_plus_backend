import calendar
from django.utils import timezone

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.contrib.gis.db import models as gis_models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(
        max_length=150,
    )

    email = models.EmailField(
        unique=True,
    )

    is_email_verified = models.BooleanField(
        default=False,
    )

    terms_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    privacy_policy_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    date_joined = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.email

class EmailVerification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verifications",
    )
    code_hash = models.CharField(
        max_length=64,
        unique=True,
    )
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Email verification for {self.user.email}"

class PasswordResetCode(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_codes",
    )

    code_hash = models.CharField(
        max_length=64,
        unique=True,
    )

    expires_at = models.DateTimeField()

    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Password reset code for {self.user.email}"

class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )

    token_hash = models.CharField(
        max_length=64,
        unique=True,
    )

    expires_at = models.DateTimeField()

    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Password reset token for {self.user.email}"

class Profile(models.Model):
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
        ("prefer_not_to_say", "Prefer not to say"),
    ]

    BLOOD_TYPE_CHOICES = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    phone_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
    )

    is_phone_verified = models.BooleanField(default=False)

    avatar = models.ImageField(
        upload_to="profiles/avatars/",
        null=True,
        blank=True,
    )

    is_donor = models.BooleanField(default=False)

    is_available = models.BooleanField(
        default=False,
    )

    last_donation = models.DateField(
        null=True,
        blank=True,
    )

    gender = models.CharField(
        max_length=30,
        choices=GENDER_CHOICES,
    )

    blood_type = models.CharField(
        max_length=3,
        choices=BLOOD_TYPE_CHOICES,
        null=True,
        blank=True,
    )

    date_of_birth = models.DateField()

    address = models.CharField(
        max_length=255,
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    location = gis_models.PointField(
        geography=True,
        srid=4326,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )
   
    @property
    def is_eligible(self):
        """
        Return whether the profile is currently eligible to donate blood.

        Eligibility is based on the interval since the last donation:
        - Male: 3 months
        - Female: 4 months
        - No previous donation: eligible
        """

        if self.last_donation is None:
            return True

        today = timezone.localdate()

        months_required = 4 if self.gender == "female" else 3

        year = self.last_donation.year
        month = self.last_donation.month + months_required

        if month > 12:
            year += (month - 1) // 12
            month = ((month - 1) % 12) + 1

        last_day = calendar.monthrange(year, month)[1]
        day = min(self.last_donation.day, last_day)

        eligible_date = self.last_donation.replace(
            year=year,
            month=month,
            day=day,
        )

        return today >= eligible_date

    def __str__(self):
        return f"Profile - {self.user.full_name}"

class PhoneVerification(models.Model):
    PROFILE_PHONE = "PROFILE_PHONE"
    BLOOD_REQUEST_CONTACT = "BLOOD_REQUEST_CONTACT"

    PURPOSE_CHOICES = [
        (PROFILE_PHONE, "Profile Phone"),
        (BLOOD_REQUEST_CONTACT, "Blood Request Contact"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="phone_verifications",
    )

    phone_number = models.CharField(
        max_length=20,
    )

    purpose = models.CharField(
        max_length=40,
        choices=PURPOSE_CHOICES,
    )

    code_hash = models.CharField(
        max_length=64,
        unique=True,
    )

    expires_at = models.DateTimeField()

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Phone verification for {self.user.email}"