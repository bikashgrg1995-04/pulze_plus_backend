from django.contrib.gis.geos import Point
from django.core.serializers import python
from django.utils import timezone
from rest_framework import serializers

from .models import BloodRequest, BloodRequestResponse


class BloodRequestSerializer(serializers.ModelSerializer):
    units_remaining = serializers.ReadOnlyField()

    class Meta:
        model = BloodRequest

        fields = [
            "id",
            "requester",
            "request_type",
            "target_donor",
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
        request = self.context.get("request")
        requester = getattr(request, "user", None)

        errors = {}

        # ---------------------------------------------------------
        # Requester / Profile validation
        # ---------------------------------------------------------
        if requester is None or not requester.is_authenticated:
            errors["requester"] = (
                "Authentication is required to create a blood request."
            )
        else:
            requester_profile = getattr(
                requester,
                "profile",
                None,
            )

            if requester_profile is None:
                errors["requester"] = (
                    "A profile is required before creating a blood request."
                )

        # ---------------------------------------------------------
        # Request type / target donor
        # ---------------------------------------------------------
        request_type = attrs.get(
            "request_type",
            getattr(
                instance,
                "request_type",
                BloodRequest.RequestType.GENERAL,
            ),
        )

        target_donor = attrs.get(
            "target_donor",
            getattr(
                instance,
                "target_donor",
                None,
            ),
        )

        valid_request_types = {
            BloodRequest.RequestType.GENERAL,
            BloodRequest.RequestType.DIRECT,
        }

        if request_type not in valid_request_types:
            errors["request_type"] = (
                "Invalid blood request type."
            )

        # ---------------------------------------------------------
        # General request
        # ---------------------------------------------------------
        if request_type == BloodRequest.RequestType.GENERAL:
            if target_donor is not None:
                errors["target_donor"] = (
                    "General requests cannot target a specific donor."
                )

        # ---------------------------------------------------------
        # Direct request
        # ---------------------------------------------------------
        elif request_type == BloodRequest.RequestType.DIRECT:
            if target_donor is None:
                errors["target_donor"] = (
                    "Direct requests must target a donor."
                )
            else:
                requester_profile = (
                    getattr(requester, "profile", None)
                    if requester is not None
                    else None
                )

                if (
                    requester_profile is not None
                    and target_donor.pk == requester_profile.pk
                ):
                    errors["target_donor"] = (
                        "You cannot send a direct blood request to yourself."
                    )

                if not target_donor.is_donor:
                    errors["target_donor"] = (
                        "The selected user is not a donor."
                    )

                if not target_donor.is_available:
                    errors["target_donor"] = (
                        "The selected donor is currently unavailable."
                    )

                if target_donor.location is None:
                    errors["target_donor"] = (
                        "The selected donor does not have a valid location."
                    )

        # ---------------------------------------------------------
        # Request type / target donor immutability
        # ---------------------------------------------------------
        if instance is not None:
            existing_request_type = instance.request_type
            existing_target_donor_id = instance.target_donor_id

            new_target_donor_id = (
                target_donor.pk
                if target_donor is not None
                else None
            )

            if (
                "request_type" in attrs
                and request_type != existing_request_type
            ):
                errors["request_type"] = (
                    "Request type cannot be changed after creation."
                )

            if (
                "target_donor" in attrs
                and new_target_donor_id != existing_target_donor_id
            ):
                errors["target_donor"] = (
                    "Target donor cannot be changed after creation."
                )

        # ---------------------------------------------------------
        # Patient / relationship validation
        # ---------------------------------------------------------
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
            getattr(
                instance,
                "other_relationship",
                "",
            ),
        ).strip()

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

        # ---------------------------------------------------------
        # Other relationship validation
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # Purpose validation
        # ---------------------------------------------------------
        purpose = attrs.get(
            "purpose",
            getattr(instance, "purpose", None),
        )

        purpose_other = attrs.get(
            "purpose_other",
            getattr(
                instance,
                "purpose_other",
                "",
            ),
        ).strip()

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

        # ---------------------------------------------------------
        # Units validation
        # ---------------------------------------------------------
        units_required = attrs.get(
            "units_required",
            getattr(
                instance,
                "units_required",
                None,
            ),
        )

        if units_required is not None and units_required < 1:
            errors["units_required"] = (
                "At least one blood unit is required."
            )

        # ---------------------------------------------------------
        # Date / time validation
        # ---------------------------------------------------------
        required_at = attrs.get(
            "required_at",
            getattr(
                instance,
                "required_at",
                None,
            ),
        )

        expires_at = attrs.get(
            "expires_at",
            getattr(
                instance,
                "expires_at",
                None,
            ),
        )

        now = timezone.now()

        if required_at and required_at <= now:
            errors["required_at"] = (
                "Required time must be in the future."
            )

        if expires_at and expires_at <= now:
            errors["expires_at"] = (
                "Expiry time must be in the future."
            )

        if (
            required_at
            and expires_at
            and expires_at <= required_at
        ):
            errors["expires_at"] = (
                "Expiry time must be later than the required time."
            )

        # ---------------------------------------------------------
        # Location validation
        # ---------------------------------------------------------
        location = attrs.get("location")

        if location is not None:
            if isinstance(location, dict):
                coordinates = location.get("coordinates")

                if (
                    not isinstance(coordinates, (list, tuple))
                    or len(coordinates) != 2
                ):
                    errors["location"] = (
                        "Location must contain longitude and "
                        "latitude coordinates."
                    )
                else:
                    try:
                        longitude = float(coordinates[0])
                        latitude = float(coordinates[1])

                        if not -180 <= longitude <= 180:
                            errors["location"] = (
                                "Invalid longitude."
                            )
                        elif not -90 <= latitude <= 90:
                            errors["location"] = (
                                "Invalid latitude."
                            )
                        else:
                            attrs["location"] = Point(
                                longitude,
                                latitude,
                                srid=4326,
                            )

                    except (TypeError, ValueError):
                        errors["location"] = (
                            "Location coordinates must be "
                            "valid numbers."
                        )

        # ---------------------------------------------------------
        # Final validation
        # ---------------------------------------------------------
        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class PublicGeneralBloodRequestSerializer(
    serializers.ModelSerializer,
):
    """
    Public read-only representation of a general blood request.

    This serializer intentionally excludes requester identity,
    target donor information, contact phone, and verification
    metadata.
    """

    units_remaining = serializers.ReadOnlyField()

    class Meta:
        model = BloodRequest

        fields = [
            "id",
            "request_type",
            "patient_type",
            "patient_name",
            "requester_relationship",
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
            "note",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


class BloodRequestResponseSerializer(
    serializers.ModelSerializer,
):
    units_remaining = serializers.SerializerMethodField()

    class Meta:
        model = BloodRequestResponse

        fields = [
            "id",
            "blood_request",
            "donor",
            "status",
            "units_completed",
            "units_remaining",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "blood_request",
            "donor",
            "status",
            "units_completed",
            "units_remaining",
            "created_at",
            "updated_at",
        ]

    def get_units_remaining(self, obj):
        return obj.blood_request.units_remaining

class AcceptedBloodRequestConnectionSerializer(
    serializers.ModelSerializer,
):
    donor_id = serializers.IntegerField(
        source="donor.pk",
        read_only=True,
    )
    donor_name = serializers.CharField(
        source="donor.user.full_name",
        read_only=True,
    )
    donor_phone = serializers.SerializerMethodField()

    response_status = serializers.CharField(
        source="status",
        read_only=True,
    )

    class Meta:
        model = BloodRequestResponse

        fields = [
            "id",
            "donor_id",
            "donor_name",
            "donor_phone",
            "response_status",
            "units_completed",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def get_donor_phone(self, obj):
        donor = obj.donor

        if not donor.is_phone_verified:
            return None

        return donor.phone_number

class AcceptedBloodRequestDetailSerializer(
    serializers.ModelSerializer,
):
    requester_name = serializers.CharField(
        source="requester.full_name",
        read_only=True,
    )

    accepted_connections = serializers.SerializerMethodField()
    request_location = serializers.SerializerMethodField()

    units_remaining = serializers.ReadOnlyField()

    class Meta:
        model = BloodRequest

        fields = [
            "id",
            "request_type",

            "requester_name",

            "accepted_connections",

            "patient_type",
            "patient_name",
            "requester_relationship",
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
            "request_location",

            "contact_type",
            "contact_phone",
            "contact_verified_at",

            "note",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def _get_current_profile(self):
        request = self.context.get("request")

        if request is None:
            return None

        if not request.user.is_authenticated:
            return None

        return getattr(
            request.user,
            "profile",
            None,
        )

    def _get_accepted_responses(self, obj):
        return (
            BloodRequestResponse.objects
            .filter(
                blood_request=obj,
                status__in=[
                    BloodRequestResponse.Status.ACCEPTED,
                    BloodRequestResponse.Status.COMPLETED,
                ],
            )
            .select_related(
                "donor",
                "donor__user",
            )
            .order_by("created_at")
        )

    def _get_current_response(self, obj):
        profile = self._get_current_profile()

        if profile is None:
            return None

        return (
            BloodRequestResponse.objects
            .filter(
                blood_request=obj,
                donor=profile,
                status__in=[
                    BloodRequestResponse.Status.ACCEPTED,
                    BloodRequestResponse.Status.COMPLETED,
                ],
            )
            .select_related(
                "donor",
                "donor__user",
            )
            .first()
        )

    def get_request_location(self, obj):
        location = obj.location

        if location is None:
            return None

        return {
            "latitude": location.y,
            "longitude": location.x,
        }

    def get_accepted_connections(self, obj):
        profile = self._get_current_profile()

        if profile is None:
            return []

        # Requester can see every accepted/completed
        # donor connection.
        if profile.user_id == obj.requester_id:
            responses = self._get_accepted_responses(obj)

        else:
            # Donor can see only their own accepted/completed
            # connection.
            current_response = self._get_current_response(obj)

            if current_response is None:
                return []

            responses = [current_response]

        return AcceptedBloodRequestConnectionSerializer(
            responses,
            many=True,
            context=self.context,
        ).data

