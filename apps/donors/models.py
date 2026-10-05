from django.db import models
from django.contrib.gis.db import models as gis_models

from apps.accounts.models import Profile
from common.constants import BLOOD_TYPE_CHOICES


class Donor(models.Model):
    USER = "USER"
    EXTERNAL = "EXTERNAL"

    DONOR_TYPE_CHOICES = [
        (USER, "User"),
        (EXTERNAL, "External"),
    ]

    APP = "APP"
    BLOOD_BANK = "BLOOD_BANK"
    ORGANIZATION = "ORGANIZATION"
    ADMIN = "ADMIN"

    SOURCE_CHOICES = [
        (APP, "App"),
        (BLOOD_BANK, "Blood Bank"),
        (ORGANIZATION, "Organization"),
        (ADMIN, "Admin"),
    ]

    donor_type = models.CharField(
        max_length=20,
        choices=DONOR_TYPE_CHOICES,
    )

    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name="donor",
        null=True,
        blank=True,
    )

    name = models.CharField(
        max_length=150,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
    )

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

    blood_type = models.CharField(
        max_length=3,
        choices=BLOOD_TYPE_CHOICES,
    )

    is_active = models.BooleanField(
        default=True,
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        if self.profile:
            return f"Donor - {self.profile.user.full_name}"

        return f"Donor - {self.name}"