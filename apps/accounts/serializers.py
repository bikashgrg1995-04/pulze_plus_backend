from django.contrib.auth import get_user_model
from rest_framework import serializers


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