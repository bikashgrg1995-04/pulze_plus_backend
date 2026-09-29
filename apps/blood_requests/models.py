from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.accounts.models import Profile


class BloodRequest(models.Model):
    class PatientType(models.TextChoices):
        MYSELF = "MYSELF", "Myself"
        SOMEONE_ELSE = "SOMEONE_ELSE", "Someone Else"

    class Relationship(models.TextChoices):
        SELF = "SELF", "Self"
        PARENT = "PARENT", "Parent"
        SPOUSE = "SPOUSE", "Spouse"
        CHILD = "CHILD", "Child"
        SIBLING = "SIBLING", "Sibling"
        RELATIVE = "RELATIVE", "Relative"
        FRIEND = "FRIEND", "Friend"
        OTHER = "OTHER", "Other"

    class Purpose(models.TextChoices):
        SURGERY = "SURGERY", "Surgery"
        ACCIDENT = "ACCIDENT", "Accident"
        EMERGENCY = "EMERGENCY", "Emergency"
        TREATMENT = "TREATMENT", "Treatment"
        CHILDBIRTH = "CHILDBIRTH", "Childbirth"
        OTHER = "OTHER", "Other"

    class Urgency(models.TextChoices):
        EMERGENCY = "EMERGENCY", "Emergency"
        URGENT = "URGENT", "Urgent"
        SCHEDULED = "SCHEDULED", "Scheduled"

    class ContactType(models.TextChoices):
        MY_PHONE = "MY_PHONE", "My Phone"
        OTHER_PHONE = "OTHER_PHONE", "Other Phone"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        FULFILLED = "FULFILLED", "Fulfilled"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blood_requests",
    )

    patient_type = models.CharField(
        max_length=20,
        choices=PatientType.choices,
    )

    patient_name = models.CharField(
        max_length=150,
    )

    requester_relationship = models.CharField(
        max_length=30,
        choices=Relationship.choices,
    )

    other_relationship = models.CharField(
        max_length=100,
        blank=True,
    )

    purpose = models.CharField(
        max_length=30,
        choices=Purpose.choices,
    )

    purpose_other = models.CharField(
        max_length=255,
        blank=True,
    )

    blood_group = models.CharField(
        max_length=3,
        choices=Profile.BLOOD_TYPE_CHOICES,
    )

    units_required = models.PositiveIntegerField()

    units_fulfilled = models.PositiveIntegerField(
        default=0,
    )

    urgency = models.CharField(
        max_length=20,
        choices=Urgency.choices,
    )

    required_at = models.DateTimeField()

    expires_at = models.DateTimeField()

    hospital_name = models.CharField(
        max_length=255,
    )

    location = gis_models.PointField(
        geography=True,
        srid=4326,
    )

    contact_type = models.CharField(
        max_length=20,
        choices=ContactType.choices,
    )

    contact_phone = models.CharField(
        max_length=20,
    )

    contact_verified_at = models.DateTimeField()

    note = models.TextField(
        max_length=500,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=Q(units_required__gte=1),
                name="blood_request_units_required_gte_1",
            ),
            models.CheckConstraint(
                condition=Q(units_fulfilled__gte=0),
                name="blood_request_units_fulfilled_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(
                    units_fulfilled__lte=F("units_required"),
                ),
                name="blood_request_units_fulfilled_lte_required",
            ),
        ]

    @property
    def units_remaining(self):
        return max(
            self.units_required - self.units_fulfilled,
            0,
        )

    def clean(self):
        errors = {}

        if self.patient_type == self.PatientType.MYSELF:
            if self.requester_relationship != self.Relationship.SELF:
                errors["requester_relationship"] = (
                    "Relationship must be SELF when the request "
                    "is for yourself."
                )

            if self.other_relationship:
                errors["other_relationship"] = (
                    "Other relationship must be empty when the "
                    "request is for yourself."
                )

        elif self.patient_type == self.PatientType.SOMEONE_ELSE:
            if self.requester_relationship == self.Relationship.SELF:
                errors["requester_relationship"] = (
                    "Relationship cannot be SELF when the request "
                    "is for someone else."
                )

        if self.requester_relationship == self.Relationship.OTHER:
            if not self.other_relationship.strip():
                errors["other_relationship"] = (
                    "Please specify the relationship."
                )
        elif self.other_relationship:
            errors["other_relationship"] = (
                "Other relationship is only allowed when "
                "relationship is OTHER."
            )

        if self.purpose == self.Purpose.OTHER:
            if not self.purpose_other.strip():
                errors["purpose_other"] = (
                    "Please specify the purpose."
                )
        elif self.purpose_other:
            errors["purpose_other"] = (
                "Purpose details are only allowed when "
                "purpose is OTHER."
            )

        if self.required_at and self.expires_at:
            if self.expires_at <= self.required_at:
                errors["expires_at"] = (
                    "Expiry time must be later than the required time."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.blood_group} blood request "
            f"#{self.pk} by {self.requester.email}"
        )