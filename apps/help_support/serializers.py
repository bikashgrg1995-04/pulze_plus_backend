from rest_framework import serializers

from .models import FAQ, SupportRequest


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = (
            "id",
            "question",
            "answer",
            "category",
            "order",
        )


class SupportRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportRequest
        fields = (
            "id",
            "request_type",
            "subject",
            "message",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "request_type",
            "status",
            "created_at",
            "updated_at",
        )