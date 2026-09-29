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
        patient_type = attrs.get("patient_type")
        relationship = attrs.get("requester_relationship")
        other_relationship = attrs.get("other_relationship", "").strip()

        purpose = attrs.get("purpose")
        purpose_other = attrs.get("purpose_other", "").strip()

        units_required = attrs.get("units_required")
        required_at = attrs.get("required_at")
        expires_at = attrs.get("expires_at")

        errors = {}

        # Patient / relationship validation.
        if patient_type == BloodRequest.PatientType.MYSELF:
            if relationship != BloodRequest.Relationship.SELF:
                errors["requester_relationship"] = (
                    "Relationship must be SELF when the request "
                    "is for yourself."
                )

            if other_relationship:
                errors["other_relationship"] = (
                    "Other relationship must be empty when the "
                    "request is for yourself."
                )

        elif patient_type == BloodRequest.PatientType.SOMEONE_ELSE:
            if relationship == BloodRequest.Relationship.SELF:
                errors["requester_relationship"] = (
                    "Relationship cannot be SELF when the request "
                    "is for someone else."
                )

        # Other relationship validation.
        if relationship == BloodRequest.Relationship.OTHER:
            if not other_relationship:
                errors["other_relationship"] = (
                    "Please specify the relationship."
                )
        elif other_relationship:
            errors["other_relationship"] = (
                "Other relationship is only allowed when "
                "relationship is OTHER."
            )

        # Other purpose validation.
        if purpose == BloodRequest.Purpose.OTHER:
            if not purpose_other:
                errors["purpose_other"] = (
                    "Please specify the purpose."
                )
        elif purpose_other:
            errors["purpose_other"] = (
                "Purpose details are only allowed when "
                "purpose is OTHER."
            )

        # Units validation.
        if units_required is not None and units_required < 1:
            errors["units_required"] = (
                "At least one blood unit is required."
            )

        # Date validation.
        if required_at and expires_at:
            if expires_at <= required_at:
                errors["expires_at"] = (
                    "Expiry time must be later than the required time."
                )

        # Note validation.
        note = attrs.get("note", "")
        if note and len(note.strip()) > 500:
            errors["note"] = (
                "Note cannot exceed 500 characters."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs