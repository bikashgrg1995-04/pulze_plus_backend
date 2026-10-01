from django.contrib.gis.geos import Point
from django.utils import timezone
from rest_framework import serializers

from .models import BloodRequest


class BloodRequestSerializer(serializers.ModelSerializer):
    units_remaining = serializers.ReadOnlyField()

    class Meta:
        model = BloodRequest
        fields = [
            "id",
            "requester",
            "patient_type",
            "patient_name",
            "requester_relationship",
            "other_relationship",
            "purpose",
            "purpose_other",
            "blood_group",
            "units_required",
            "units_fulfilled",
            "units_remaining",
            "urgency",
            "required_at",
            "expires_at",
            "hospital_name",
            "location",
            "contact_type",
            "contact_phone",
            "contact_verified_at",
            "note",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "requester",
            "units_fulfilled",
            "units_remaining",
            "contact_verified_at",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        instance = self.instance

        patient_type = attrs.get(
            "patient_type",
            getattr(instance, "patient_type", None),
        )
        relationship = attrs.get(
            "requester_relationship",
            getattr(instance, "requester_relationship", None),
        )
        other_relationship = attrs.get(
            "other_relationship",
            getattr(instance, "other_relationship", ""),
        ).strip()

        purpose = attrs.get(
            "purpose",
            getattr(instance, "purpose", None),
        )
        purpose_other = attrs.get(
            "purpose_other",
            getattr(instance, "purpose_other", ""),
        ).strip()

        units_required = attrs.get(
            "units_required",
            getattr(instance, "units_required", None),
        )

        required_at = attrs.get(
            "required_at",
            getattr(instance, "required_at", None),
        )
        expires_at = attrs.get(
            "expires_at",
            getattr(instance, "expires_at", None),
        )

        errors = {}

        # Patient / relationship validation
        if patient_type == BloodRequest.PatientType.MYSELF:
            if relationship != BloodRequest.Relationship.SELF:
                errors["requester_relationship"] = (
                    "Relationship must be SELF when the request is for yourself."
                )

            if other_relationship:
                errors["other_relationship"] = (
                    "Other relationship must be empty when the request is for yourself."
                )

        elif patient_type == BloodRequest.PatientType.SOMEONE_ELSE:
            if relationship == BloodRequest.Relationship.SELF:
                errors["requester_relationship"] = (
                    "Relationship cannot be SELF when the request is for someone else."
                )

        # Other relationship
        if relationship == BloodRequest.Relationship.OTHER:
            if not other_relationship:
                errors["other_relationship"] = (
                    "Please specify the relationship."
                )
        elif other_relationship:
            errors["other_relationship"] = (
                "Other relationship is only allowed when relationship is OTHER."
            )

        # Purpose validation
        if purpose == BloodRequest.Purpose.OTHER:
            if not purpose_other:
                errors["purpose_other"] = (
                    "Please specify the purpose."
                )
        elif purpose_other:
            errors["purpose_other"] = (
                "Purpose details are only allowed when purpose is OTHER."
            )

        # Units
        if units_required is not None and units_required < 1:
            errors["units_required"] = (
                "At least one blood unit is required."
            )

        # Date/time
        now = timezone.now()

        if required_at and required_at <= now:
            errors["required_at"] = (
                "Required time must be in the future."
            )

        if expires_at and expires_at <= now:
            errors["expires_at"] = (
                "Expiry time must be in the future."
            )

        if required_at and expires_at and expires_at <= required_at:
            errors["expires_at"] = (
                "Expiry time must be later than the required time."
            )

        # Location
        location = attrs.get("location")

        if location is not None:
            if isinstance(location, dict):
                coordinates = location.get("coordinates")

                if (
                    not isinstance(coordinates, (list, tuple))
                    or len(coordinates) != 2
                ):
                    errors["location"] = (
                        "Location must contain longitude and latitude coordinates."
                    )
                else:
                    try:
                        longitude = float(coordinates[0])
                        latitude = float(coordinates[1])

                        if not (-180 <= longitude <= 180):
                            errors["location"] = "Invalid longitude."
                        elif not (-90 <= latitude <= 90):
                            errors["location"] = "Invalid latitude."
                        else:
                            attrs["location"] = Point(
                                longitude,
                                latitude,
                                srid=4326,
                            )

                    except (TypeError, ValueError):
                        errors["location"] = (
                            "Location coordinates must be valid numbers."
                        )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs