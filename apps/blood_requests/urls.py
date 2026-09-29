from django.urls import path

from .views import (
    BloodRequestDetailView,
    BloodRequestListCreateView,
)

urlpatterns = [
    path(
        "",
        BloodRequestListCreateView.as_view(),
        name="blood-request-list-create",
    ),
    path(
        "<int:pk>/",
        BloodRequestDetailView.as_view(),
        name="blood-request-detail",
    ),
]