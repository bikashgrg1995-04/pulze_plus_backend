"""
URL configuration for the Pulze+ backend project.

This file defines the main URL routing for the Django project.
Feature-specific URLs are kept inside their respective apps.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    # Django Admin
    # Used for managing users and backend data through the admin panel.
    path("admin/", admin.site.urls),

    # Core API
    # Project-wide/system endpoints that do not belong to a specific feature.
    # Example: GET /api/v1/health/
    path(
        "api/v1/",
        include("core.urls"),
    ),

    # Accounts & Authentication API
    # User registration, login, email verification, phone verification, etc.
    # Example: POST /api/v1/auth/register/
    path(
        "api/v1/auth/",
        include("apps.accounts.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )