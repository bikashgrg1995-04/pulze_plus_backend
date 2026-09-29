from django.utils import timezone

from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.accounts.models import PhoneVerification

from .models import BloodRequest
from .serializers import BloodRequestSerializer


class BloodRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BloodRequestSerializer

    def get_queryset(self):
        queryset = BloodRequest.objects.filter(
            requester=self.request.user,
        ).select_related(
            "requester",
        )

        self._expire_requests(queryset)

        return queryset

    @staticmethod
    def _expire_requests(queryset):
        now = timezone.now()

        queryset.filter(
            status=BloodRequest.Status.ACTIVE,
            expires_at__lte=now,
        ).update(
            status=BloodRequest.Status.EXPIRED,
            updated_at=now,
        )

    def perform_create(self, serializer):
        contact_phone = serializer.validated_data["contact_phone"]
        now = timezone.now()

        profile = getattr(self.request.user, "profile", None)

        # Case 1: The user's profile phone is already verified.
        profile_phone_verified = (
            profile is not None
            and profile.phone_number == contact_phone
            and profile.is_phone_verified
        )

        # Case 2: This phone was separately verified for this blood request.
        request_phone_verification = (
            PhoneVerification.objects
            .filter(
                user=self.request.user,
                phone_number=contact_phone,
                purpose=PhoneVerification.BLOOD_REQUEST_CONTACT,
                verified_at__isnull=False,
                used_at__isnull=True,
                expires_at__gt=now,
            )
            .order_by("-created_at")
            .first()
        )

        # At least one verification source must be valid.
        if not profile_phone_verified and request_phone_verification is None:
            raise ValidationError(
                {
                    "contact_phone": (
                        "This phone number must be verified "
                        "before creating a blood request."
                    )
                }
            )

        serializer.save(
            requester=self.request.user,
            contact_verified_at=now,
        )

        # A request-specific phone verification is single-use.
        if request_phone_verification is not None:
            request_phone_verification.used_at = now
            request_phone_verification.save(
                update_fields=["used_at"],
            )


class BloodRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BloodRequestSerializer

    def get_queryset(self):
        queryset = BloodRequest.objects.filter(
            requester=self.request.user,
        ).select_related(
            "requester",
        )

        self._expire_requests(queryset)

        return queryset

    @staticmethod
    def _expire_requests(queryset):
        now = timezone.now()

        queryset.filter(
            status=BloodRequest.Status.ACTIVE,
            expires_at__lte=now,
        ).update(
            status=BloodRequest.Status.EXPIRED,
            updated_at=now,
        )

    def _get_active_request(self):
        blood_request = self.get_object()

        if blood_request.status == BloodRequest.Status.ACTIVE:
            return blood_request

        raise ValidationError(
            {
                "status": (
                    f"This blood request is already "
                    f"{blood_request.status.lower()} and cannot be modified."
                )
            }
        )

    def perform_update(self, serializer):
        blood_request = self._get_active_request()

        serializer.save(
            requester=blood_request.requester,
        )

    def destroy(self, request, *args, **kwargs):
        blood_request = self._get_active_request()

        now = timezone.now()

        blood_request.status = BloodRequest.Status.CANCELLED
        blood_request.updated_at = now

        blood_request.save(
            update_fields=[
                "status",
                "updated_at",
            ],
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )