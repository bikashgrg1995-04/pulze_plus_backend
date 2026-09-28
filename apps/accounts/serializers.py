from django.contrib.auth import get_user_model

from rest_framework import serializers
from django.utils import timezone

from .models import Profile


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    terms_accepted = serializers.BooleanField(
        write_only=True,
        required=True,
    )

    privacy_policy_accepted = serializers.BooleanField(
        write_only=True,
        required=True,
    )

    class Meta:
        model = User
        fields = (
            "full_name",
            "email",
            "password",
            "terms_accepted",
            "privacy_policy_accepted",
        )

    def validate(self, attrs):
        if not attrs["terms_accepted"]:
            raise serializers.ValidationError(
                {
                    "terms_accepted": (
                        "You must accept the Terms & Conditions."
                    )
                }
            )

        if not attrs["privacy_policy_accepted"]:
            raise serializers.ValidationError(
                {
                    "privacy_policy_accepted": (
                        "You must accept the Privacy Policy."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("terms_accepted")
        validated_data.pop("privacy_policy_accepted")

        password = validated_data.pop("password")

        accepted_at = timezone.now()

        user = User.objects.create_user(
            password=password,
            terms_accepted_at=accepted_at,
            privacy_policy_accepted_at=accepted_at,
            **validated_data,
        )

        return user

class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(read_only=True)
    is_donor = serializers.BooleanField(read_only=True)

    class Meta:
        model = Profile
        fields = (
            "phone_number",
            "avatar",
            "is_donor",
            "blood_type",
            "gender",
            "date_of_birth",
            "address",
            "city",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")

        if instance.avatar and request:
            data["avatar"] = request.build_absolute_uri(
                instance.avatar.url
            )
        else:
            data["avatar"] = None

        return data
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    code = serializers.CharField(
        min_length=6,
        max_length=6,
    )

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "Verification code must contain only digits."
            )

        return value

class ResetPasswordSerializer(serializers.Serializer):
    reset_token = serializers.CharField()

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {
                    "confirm_password": "Passwords do not match."
                }
            )

        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
    )

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {
                    "confirm_password": "Passwords do not match."
                }
            )

        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {
                    "new_password": (
                        "New password must be different "
                        "from your current password."
                    )
                }
            )

        return attrs