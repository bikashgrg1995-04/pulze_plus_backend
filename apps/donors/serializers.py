from rest_framework import serializers

from apps.accounts.models import Profile

from .models import Donor


class DonorListSerializer(serializers.ModelSerializer):
    """
    App-registered donors.
    """

    distance_km = serializers.SerializerMethodField()
    is_eligible = serializers.ReadOnlyField()

    class Meta:
        model = Profile
        fields = (
            "id",
            "blood_type",
            "phone_number",
            "is_phone_verified",
            "is_available",
            "is_eligible",
            "last_donation",
            "distance_km",
        )

    def get_distance_km(self, obj):
        if not hasattr(obj, "distance") or obj.distance is None:
            return None

        return round(obj.distance.km, 2)


class ExternalDonorListSerializer(serializers.ModelSerializer):
    """
    External donors added by blood banks,
    organizations, or admins.
    """

    class Meta:
        model = Donor
        fields = (
            "id",
            "name",
            "phone_number",
            "blood_type",
            "address",
            "city",
            "source",
        )