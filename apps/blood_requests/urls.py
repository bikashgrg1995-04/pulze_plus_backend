
from django.urls import path

from .views import (
    AcceptedBloodRequestDetailView,
    BloodRequestAcceptView,
    BloodRequestCompletionView,
    BloodRequestDeclineView,
    BloodRequestDetailView,
    BloodRequestListCreateView,
    GeneralBloodRequestListView,
    IncomingDirectBloodRequestListView,
)


urlpatterns = [
    # ---------------------------------------------------------
    # My blood requests
    # ---------------------------------------------------------
    path(
        "",
        BloodRequestListCreateView.as_view(),
        name="blood-request-list-create",
    ),

    # ---------------------------------------------------------
    # Discoverable general requests
    # ---------------------------------------------------------
    path(
        "general/",
        GeneralBloodRequestListView.as_view(),
        name="general-blood-request-list",
    ),

    # ---------------------------------------------------------
    # Direct requests received by the authenticated donor
    # ---------------------------------------------------------
    path(
        "incoming/",
        IncomingDirectBloodRequestListView.as_view(),
        name="incoming-direct-blood-request-list",
    ),

    # ---------------------------------------------------------
    # Request detail / update / cancel
    # ---------------------------------------------------------
    path(
        "<int:pk>/",
        BloodRequestDetailView.as_view(),
        name="blood-request-detail",
    ),

    # ---------------------------------------------------------
    # Donor response actions
    # ---------------------------------------------------------
    path(
        "<int:pk>/accept/",
        BloodRequestAcceptView.as_view(),
        name="blood-request-accept",
    ),
    path(
        "<int:pk>/decline/",
        BloodRequestDeclineView.as_view(),
        name="blood-request-decline",
    ),
    path(
        "<int:pk>/complete/",
        BloodRequestCompletionView.as_view(),
        name="blood-request-complete",
    ),

    # ---------------------------------------------------------
    # Accepted connection detail
    # ---------------------------------------------------------
    path(
        "<int:pk>/connection/",
        AcceptedBloodRequestDetailView.as_view(),
        name="accepted-blood-request-connection",
    ),
]