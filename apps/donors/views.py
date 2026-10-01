
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Q

from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from apps.accounts.models import Profile

from .pagination import DonorPagination
from .serializers import DonorListSerializer


class DonorListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = DonorListSerializer
    pagination_class = DonorPagination

    def get_queryset(self):
        search = self.request.query_params.get("search")
        blood_type = self.request.query_params.get("blood_type")

        latitude = self.request.query_params.get("latitude")
        longitude = self.request.query_params.get("longitude")
        radius = self.request.query_params.get("radius")

        queryset = Profile.objects.filter(
            is_donor=True,
            is_available=True,
            location__isnull=False,
        )

        # Exclude the currently authenticated user
        # from the donor discovery list.
        if self.request.user.is_authenticated:
            queryset = queryset.exclude(
                user=self.request.user,
            )

        # Search filter
        # Search only public discovery fields.
        # Donor name, email, and phone are intentionally
        # excluded from search.
        if search:
            search = search.strip()

            if search:
                queryset = queryset.filter(
                    Q(city__icontains=search)
                    | Q(address__icontains=search)
                )

        # Blood group filter
        if blood_type:
            valid_blood_types = {
                choice[0]
                for choice in Profile.BLOOD_TYPE_CHOICES
            }

            if blood_type not in valid_blood_types:
                raise ValidationError(
                    {
                        "message": "Invalid blood type.",
                        "errors": {
                            "blood_type": "Invalid blood type.",
                        },
                    }
                )

            queryset = queryset.filter(
                blood_type=blood_type,
            )

        # Nearby filter
        # Location is optional. Distance filtering happens
        # only when latitude and longitude are provided.
        if latitude is not None or longitude is not None:
            if latitude is None or longitude is None:
                raise ValidationError(
                    {
                        "message": (
                            "Latitude and longitude are required "
                            "for nearby filtering."
                        ),
                        "errors": {
                            "location": (
                                "Both latitude and longitude "
                                "are required."
                            ),
                        },
                    }
                )

            if radius is None:
                radius = "50"

            try:
                latitude = float(latitude)
                longitude = float(longitude)
                radius = float(radius)
            except (TypeError, ValueError):
                raise ValidationError(
                    {
                        "message": (
                            "Latitude, longitude, and radius "
                            "must be valid numbers."
                        ),
                        "errors": {
                            "location": "Invalid location or radius.",
                        },
                    }
                )

            if not -90 <= latitude <= 90:
                raise ValidationError(
                    {
                        "message": "Latitude must be between -90 and 90.",
                        "errors": {
                            "latitude": "Invalid latitude.",
                        },
                    }
                )

            if not -180 <= longitude <= 180:
                raise ValidationError(
                    {
                        "message": (
                            "Longitude must be between -180 and 180."
                        ),
                        "errors": {
                            "longitude": "Invalid longitude.",
                        },
                    }
                )

            if radius <= 0 or radius > 50:
                raise ValidationError(
                    {
                        "message": (
                            "Radius must be greater than 0 "
                            "and cannot exceed 50 km."
                        ),
                        "errors": {
                            "radius": (
                                "Radius must be between 0 and 50 km."
                            ),
                        },
                    }
                )

            requester_location = Point(
                longitude,
                latitude,
                srid=4326,
            )

            queryset = (
                queryset
                .annotate(
                    distance=Distance(
                        "location",
                        requester_location,
                    ),
                )
                .filter(
                    location__distance_lte=(
                        requester_location,
                        D(km=radius),
                    ),
                )
                .order_by("distance")
            )

        else:
            # No nearby filter.
            # Keep normal donor list ordering.
            queryset = queryset.order_by("-updated_at")

        return queryset
