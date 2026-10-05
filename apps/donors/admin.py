from django.contrib import admin

from .models import Donor


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "donor_type",
        "name",
        "phone_number",
        "blood_type",
        "is_active",
        "source",
        "created_at",
    )

    list_filter = (
        "donor_type",
        "blood_type",
        "is_active",
        "source",
    )

    search_fields = (
        "name",
        "phone_number",
        "profile__user__full_name",
        "profile__user__email",
    )

    ordering = ("-created_at",)