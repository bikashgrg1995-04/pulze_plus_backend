from django.urls import path

from .views import (
    DonorListView,
    ExternalDonorListView,
)


urlpatterns = [
    path(
        "",
        DonorListView.as_view(),
        name="donor-list",
    ),
    path(
        "external/",
        ExternalDonorListView.as_view(),
        name="external-donor-list",
    ),
]