from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import FAQ, SupportRequest
from .serializers import (
    FAQSerializer,
    SupportRequestSerializer,
)


class FAQListView(generics.ListAPIView):
    serializer_class = FAQSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return FAQ.objects.filter(
            is_active=True,
        ).order_by(
            "order",
            "-created_at",
        )


class SupportRequestCreateView(generics.CreateAPIView):
    serializer_class = SupportRequestSerializer
    permission_classes = [IsAuthenticated]

    request_type = None

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            request_type=self.request_type,
        )


class ContactSupportCreateView(SupportRequestCreateView):
    request_type = SupportRequest.RequestType.CONTACT


class ReportProblemCreateView(SupportRequestCreateView):
    request_type = SupportRequest.RequestType.PROBLEM


class FeedbackCreateView(SupportRequestCreateView):
    request_type = SupportRequest.RequestType.FEEDBACK
