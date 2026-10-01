
import calendar
from datetime import date

from rest_framework import serializers

from apps.accounts.models import Profile


class DonorListSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()
    is_eligible = serializers.SerializerMethodField()

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

    def get_is_eligible(self, obj):
        if obj.last_donation is None:
            return True

        if obj.gender == "male":
            waiting_months = 3
        elif obj.gender == "female":
            waiting_months = 4
        else:
            return True

        eligible_date = self._add_months(
            obj.last_donation,
            waiting_months,
        )

        return date.today() >= eligible_date

    @staticmethod
    def _add_months(value, months):
        month = value.month - 1 + months
        year = value.year + month // 12
        month = month % 12 + 1

        day = min(
            value.day,
            calendar.monthrange(year, month)[1],
        )

        return value.replace(
            year=year,
            month=month,
            day=day,
        )
