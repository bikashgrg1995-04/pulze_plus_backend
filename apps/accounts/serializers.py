from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.gis.geos import Point

from .models import Profile


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = (
            "full_name",
            "email",
            "password",
            "phone_number",
        )
        extra_kwargs = {
            "phone_number": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
        }

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data,
        )

        return user

class ProfileSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(
        required=False,
        allow_null=True,
    )
    longitude = serializers.FloatField(
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Profile
        fields = (
            "gender",
            "date_of_birth",
            "address",
            "city",
            "latitude",
            "longitude",
        )

    def validate(self, attrs):
        latitude = attrs.pop("latitude", serializers.empty)
        longitude = attrs.pop("longitude", serializers.empty)

        # If one coordinate is provided, the other is also required.
        if (
            latitude is not serializers.empty
            and longitude is serializers.empty
        ) or (
            latitude is serializers.empty
            and longitude is not serializers.empty
        ):
            raise serializers.ValidationError(
                "Latitude and longitude must be provided together."
            )

        # Coordinates were not included.
        if latitude is serializers.empty:
            return attrs

        # Explicitly remove the location.
        if latitude is None and longitude is None:
            attrs["location"] = None
            return attrs

        if latitude is None or longitude is None:
            raise serializers.ValidationError(
                "Latitude and longitude must both have a value."
            )

        if not -90 <= latitude <= 90:
            raise serializers.ValidationError(
                {"latitude": "Latitude must be between -90 and 90."}
            )

        if not -180 <= longitude <= 180:
            raise serializers.ValidationError(
                {"longitude": "Longitude must be between -180 and 180."}
            )

        attrs["location"] = Point(
            longitude,
            latitude,
            srid=4326,
        )

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.location is None:
            data["latitude"] = None
            data["longitude"] = None
        else:
            data["latitude"] = instance.location.y
            data["longitude"] = instance.location.x

        return data