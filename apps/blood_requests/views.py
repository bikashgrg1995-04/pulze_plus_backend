from django.db import transaction
from django.utils import timezone

from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import PhoneVerification

from .models import BloodRequest, BloodRequestResponse
from .serializers import (
    AcceptedBloodRequestDetailSerializer,
    BloodRequestResponseSerializer,
    BloodRequestSerializer,
    PublicGeneralBloodRequestSerializer,
)


class BloodRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BloodRequestSerializer

    def get_queryset(self):
        queryset = (
            BloodRequest.objects
            .filter(
                requester=self.request.user,
            )
            .select_related(
                "requester",
                "target_donor",
            )
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

        profile = getattr(
            self.request.user,
            "profile",
            None,
        )

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

        if (
            not profile_phone_verified
            and request_phone_verification is None
        ):
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


class BloodRequestDetailView(
    generics.RetrieveUpdateDestroyAPIView,
):
    permission_classes = [IsAuthenticated]
    serializer_class = BloodRequestSerializer

    def get_queryset(self):
        queryset = (
            BloodRequest.objects
            .filter(
                requester=self.request.user,
            )
            .select_related(
                "requester",
                "target_donor",
            )
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

class GeneralBloodRequestListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PublicGeneralBloodRequestSerializer

    def get_queryset(self):
        now = timezone.now()

        BloodRequest.objects.filter(
            status=BloodRequest.Status.ACTIVE,
            expires_at__lte=now,
        ).update(
            status=BloodRequest.Status.EXPIRED,
            updated_at=now,
        )

        return (
            BloodRequest.objects.filter(
                request_type=BloodRequest.RequestType.GENERAL,
                status=BloodRequest.Status.ACTIVE,
                expires_at__gt=now,
            )
            .select_related(
                "requester",
                "target_donor",
                "target_donor__user",
            )
            .order_by("-created_at")
        )

class IncomingDirectBloodRequestListView(
    generics.ListAPIView,
):
    """
    Returns active direct blood requests targeted at the
    authenticated user's donor profile.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = BloodRequestSerializer

    def get_queryset(self):
        profile = getattr(
            self.request.user,
            "profile",
            None,
        )

        if profile is None:
            return BloodRequest.objects.none()

        now = timezone.now()

        queryset = (
            BloodRequest.objects
            .filter(
                request_type=BloodRequest.RequestType.DIRECT,
                target_donor=profile,
                status=BloodRequest.Status.ACTIVE,
                expires_at__gt=now,
            )
            .select_related(
                "requester",
                "target_donor",
            )
            .order_by("-created_at")
        )

        return queryset

class BloodRequestAcceptView(APIView):
    """
    Accept a general or direct blood request.

    Acceptance requirements:
    - authenticated user must have a profile
    - user must be eligible to donate
    - user blood group must match the request
    - request must still be active
    - request must not be expired
    - requester cannot accept their own request
    - direct request can only be accepted by target user

    IMPORTANT:
    - is_donor is not required for acceptance
    - is_available is not required for acceptance
    - location is not required for acceptance
    """

    permission_classes = [IsAuthenticated]

    @staticmethod
    def _get_donor_profile(user):
        profile = getattr(
            user,
            "profile",
            None,
        )

        if profile is None:
            raise ValidationError(
                {
                    "donor": (
                        "A profile is required to respond "
                        "to a blood request."
                    )
                }
            )

        return profile

    def post(self, request, pk):
        donor_profile = self._get_donor_profile(
            request.user,
        )

        with transaction.atomic():
            blood_request = (
                BloodRequest.objects
                .select_for_update()
                
                .filter(
                    pk=pk,
                )
                .first()
            )

            if blood_request is None:
                raise ValidationError(
                    {
                        "blood_request": (
                            "Blood request not found."
                        )
                    }
                )

            now = timezone.now()

            # Handle expiry before accepting.
            if (
                blood_request.status == BloodRequest.Status.ACTIVE
                and blood_request.expires_at <= now
            ):
                blood_request.status = BloodRequest.Status.EXPIRED
                blood_request.updated_at = now
                blood_request.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ],
                )

                raise ValidationError(
                    {
                        "status": (
                            "This blood request has expired."
                        )
                    }
                )

            if blood_request.status != BloodRequest.Status.ACTIVE:
                raise ValidationError(
                    {
                        "status": (
                            f"This blood request is already "
                            f"{blood_request.status.lower()}."
                        )
                    }
                )

            if blood_request.requester_id == request.user.id:
                raise ValidationError(
                    {
                        "blood_request": (
                            "You cannot accept your own "
                            "blood request."
                        )
                    }
                )

            # Direct requests can only be accepted by the
            # specifically targeted donor.
            if (
                blood_request.request_type
                == BloodRequest.RequestType.DIRECT
                and blood_request.target_donor_id
                != donor_profile.pk
            ):
                raise ValidationError(
                    {
                        "blood_request": (
                            "This direct blood request is not "
                            "targeted to you."
                        )
                    }
                )

            if not donor_profile.is_phone_verified:
                raise ValidationError(
                    {
                        "phone_number": (
                            "A verified phone number is required "
                            "to accept a blood request."
                        )
                    }
                )

            # A donor must still be eligible at acceptance time.
            if not donor_profile.is_eligible:
                raise ValidationError(
                    {
                        "donor": (
                            "You are currently not eligible "
                            "to donate blood."
                        )
                    }
                )

            # Blood group must match.
            if donor_profile.blood_type != blood_request.blood_group:
                raise ValidationError(
                    {
                        "blood_group": (
                            "Your blood group does not match "
                            "this blood request."
                        )
                    }
                )

            existing_response = (
                BloodRequestResponse.objects
                .select_for_update()
                .filter(
                    blood_request=blood_request,
                    donor=donor_profile,
                )
                .first()
            )

            if existing_response is not None:
                if (
                    existing_response.status
                    == BloodRequestResponse.Status.ACCEPTED
                ):
                    raise ValidationError(
                        {
                            "response": (
                                "You have already accepted "
                                "this blood request."
                            )
                        }
                    )

                if (
                    existing_response.status
                    == BloodRequestResponse.Status.COMPLETED
                ):
                    raise ValidationError(
                        {
                            "response": (
                                "Your response for this request "
                                "is already completed."
                            )
                        }
                    )

                if (
                    existing_response.status
                    == BloodRequestResponse.Status.DECLINED
                ):
                    existing_response.status = (
                        BloodRequestResponse.Status.ACCEPTED
                    )
                    existing_response.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ],
                    )

                    serializer = BloodRequestResponseSerializer(
                        existing_response,
                        context={"request": request},
                    )

                    return Response(
                        serializer.data,
                        status=status.HTTP_200_OK,
                    )

            response = BloodRequestResponse.objects.create(
                blood_request=blood_request,
                donor=donor_profile,
                status=BloodRequestResponse.Status.ACCEPTED,
            )

            serializer = BloodRequestResponseSerializer(
                response,
                context={"request": request},
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

class BloodRequestDeclineView(APIView):
    """
    Decline a blood request.

    General request:
        Any eligible/matching donor can decline after it has
        been received/previously responded to.

    Direct request:
        Only the targeted donor can decline.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        donor_profile = getattr(
            request.user,
            "profile",
            None,
        )

        if donor_profile is None:
            raise ValidationError(
                {
                    "donor": (
                        "A profile is required to respond "
                        "to a blood request."
                    )
                }
            )

        if not donor_profile.is_donor:
            raise ValidationError(
                {
                    "donor": (
                        "Only registered donors can respond "
                        "to blood requests."
                    )
                }
            )

        with transaction.atomic():
            blood_request = (
                BloodRequest.objects
                .select_for_update()
                .filter(
                    pk=pk,
                )
                .first()
            )

            if blood_request is None:
                raise ValidationError(
                    {
                        "blood_request": (
                            "Blood request not found."
                        )
                    }
                )

            now = timezone.now()

            if (
                blood_request.status == BloodRequest.Status.ACTIVE
                and blood_request.expires_at <= now
            ):
                blood_request.status = BloodRequest.Status.EXPIRED
                blood_request.updated_at = now
                blood_request.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ],
                )

                raise ValidationError(
                    {
                        "status": (
                            "This blood request has expired."
                        )
                    }
                )

            if blood_request.status != BloodRequest.Status.ACTIVE:
                raise ValidationError(
                    {
                        "status": (
                            f"This blood request is already "
                            f"{blood_request.status.lower()}."
                        )
                    }
                )

            if blood_request.requester_id == request.user.id:
                raise ValidationError(
                    {
                        "blood_request": (
                            "You cannot decline your own "
                            "blood request."
                        )
                    }
                )

            if (
                blood_request.request_type
                == BloodRequest.RequestType.DIRECT
                and blood_request.target_donor_id
                != donor_profile.pk
            ):
                raise ValidationError(
                    {
                        "blood_request": (
                            "This direct blood request is not "
                            "targeted to you."
                        )
                    }
                )

            response = (
                BloodRequestResponse.objects
                .select_for_update()
                .filter(
                    blood_request=blood_request,
                    donor=donor_profile,
                )
                .first()
            )

            if response is None:
                response = BloodRequestResponse.objects.create(
                    blood_request=blood_request,
                    donor=donor_profile,
                    status=BloodRequestResponse.Status.DECLINED,
                )
            else:
                if (
                    response.status
                    == BloodRequestResponse.Status.COMPLETED
                ):
                    raise ValidationError(
                        {
                            "response": (
                                "A completed response cannot "
                                "be declined."
                            )
                        }
                    )

                if (
                    response.status
                    == BloodRequestResponse.Status.ACCEPTED
                    and response.units_completed > 0
                ):
                    raise ValidationError(
                        {
                            "response": (
                                "A response with completed units "
                                "cannot be declined."
                            )
                        }
                    )

                response.status = (
                    BloodRequestResponse.Status.DECLINED
                )
                response.units_completed = 0
                response.save(
                    update_fields=[
                        "status",
                        "units_completed",
                        "updated_at",
                    ],
                )

            serializer = BloodRequestResponseSerializer(
                response,
                context={"request": request},
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

class BloodRequestCompletionView(APIView):
    """
    Record actual donated blood units.

    Completion is a historical donation record. It does not depend
    on the user's current donor status or availability.

    A user may complete multiple donation units across multiple
    completion actions until the request is fully fulfilled.

    Accepting a request does not change units_fulfilled.
    Only this endpoint changes fulfillment counts.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        donor_profile = getattr(
            request.user,
            "profile",
            None,
        )

        if donor_profile is None:
            raise ValidationError(
                {
                    "donor": (
                        "A profile is required to complete "
                        "a blood donation."
                    )
                }
            )

        units_completed = request.data.get("units_completed")

        try:
            units_completed = int(units_completed)
        except (TypeError, ValueError):
            raise ValidationError(
                {
                    "units_completed": (
                        "Units completed must be a valid integer."
                    )
                }
            )

        if units_completed < 1:
            raise ValidationError(
                {
                    "units_completed": (
                        "At least one completed unit is required."
                    )
                }
            )

        with transaction.atomic():
            blood_request = (
                BloodRequest.objects
                .select_for_update()
                .filter(
                    pk=pk,
                )
                .first()
            )

            if blood_request is None:
                raise ValidationError(
                    {
                        "blood_request": (
                            "Blood request not found."
                        )
                    }
                )

            now = timezone.now()

            if (
                blood_request.status == BloodRequest.Status.ACTIVE
                and blood_request.expires_at <= now
            ):
                blood_request.status = BloodRequest.Status.EXPIRED
                blood_request.updated_at = now
                blood_request.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ],
                )

                raise ValidationError(
                    {
                        "status": (
                            "This blood request has expired."
                        )
                    }
                )

            if blood_request.status != BloodRequest.Status.ACTIVE:
                raise ValidationError(
                    {
                        "status": (
                            f"This blood request is already "
                            f"{blood_request.status.lower()}."
                        )
                    }
                )

            if blood_request.requester_id == request.user.id:
                raise ValidationError(
                    {
                        "blood_request": (
                            "The requester cannot record "
                            "a donor completion."
                        )
                    }
                )

            if (
                blood_request.request_type
                == BloodRequest.RequestType.DIRECT
                and blood_request.target_donor_id
                != donor_profile.pk
            ):
                raise ValidationError(
                    {
                        "blood_request": (
                            "This direct blood request is not "
                            "targeted to you."
                        )
                    }
                )

            response = (
                BloodRequestResponse.objects
                .select_for_update()
                .filter(
                    blood_request=blood_request,
                    donor=donor_profile,
                    status__in=[
                        BloodRequestResponse.Status.ACCEPTED,
                        BloodRequestResponse.Status.COMPLETED,
                    ],
                )
                .first()
            )

            if response is None:
                raise ValidationError(
                    {
                        "response": (
                            "You must accept the blood request "
                            "before recording a donation."
                        )
                    }
                )

            remaining_units = (
                blood_request.units_required
                - blood_request.units_fulfilled
            )

            if remaining_units <= 0:
                raise ValidationError(
                    {
                        "blood_request": (
                            "This blood request is already "
                            "fully fulfilled."
                        )
                    }
                )

            if units_completed > remaining_units:
                raise ValidationError(
                    {
                        "units_completed": (
                            f"Only {remaining_units} unit(s) "
                            "remain to fulfill this request."
                        )
                    }
                )

            response.units_completed += units_completed
            response.status = (
                BloodRequestResponse.Status.COMPLETED
            )

            response.save(
                update_fields=[
                    "units_completed",
                    "status",
                    "updated_at",
                ],
            )

            blood_request.units_fulfilled += units_completed

            if (
                blood_request.units_fulfilled
                >= blood_request.units_required
            ):
                blood_request.units_fulfilled = (
                    blood_request.units_required
                )
                blood_request.status = (
                    BloodRequest.Status.FULFILLED
                )

            blood_request.updated_at = now

            blood_request.save(
                update_fields=[
                    "units_fulfilled",
                    "status",
                    "updated_at",
                ],
            )

            serializer = BloodRequestResponseSerializer(
                response,
                context={"request": request},
            )

            return Response(
                {
                    "response": serializer.data,
                    "units_fulfilled": (
                        blood_request.units_fulfilled
                    ),
                    "units_remaining": (
                        blood_request.units_remaining
                    ),
                    "request_status": (
                        blood_request.status
                    ),
                },
                status=status.HTTP_200_OK,
            )

class AcceptedBloodRequestDetailView(APIView):
    """
    Return accepted blood-request connection details.

    Access is allowed for:
    - the original requester
    - a donor with an ACCEPTED or COMPLETED response

    Requesters can see all accepted/completed donor connections.

    Donors can see only their own accepted/completed connection.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = getattr(
            request.user,
            "profile",
            None,
        )

        if profile is None:
            raise ValidationError(
                {
                    "profile": (
                        "A profile is required to access "
                        "this blood request."
                    )
                }
            )

        blood_request = (
            BloodRequest.objects
            .select_related(
                "requester",
            )
            .filter(
                pk=pk,
            )
            .first()
        )

        if blood_request is None:
            raise ValidationError(
                {
                    "blood_request": (
                        "Blood request not found."
                    )
                }
            )

        # -----------------------------------------------------
        # Requester access
        # -----------------------------------------------------
        if blood_request.requester_id == request.user.id:
            serializer = AcceptedBloodRequestDetailSerializer(
                blood_request,
                context={
                    "request": request,
                },
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        # -----------------------------------------------------
        # Accepted donor access
        # -----------------------------------------------------
        connection_exists = (
            BloodRequestResponse.objects
            .filter(
                blood_request=blood_request,
                donor=profile,
                status__in=[
                    BloodRequestResponse.Status.ACCEPTED,
                    BloodRequestResponse.Status.COMPLETED,
                ],
            )
            .exists()
        )

        if not connection_exists:
            raise ValidationError(
                {
                    "access": (
                        "You do not have an accepted connection "
                        "for this blood request."
                    )
                }
            )

        serializer = AcceptedBloodRequestDetailSerializer(
            blood_request,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


