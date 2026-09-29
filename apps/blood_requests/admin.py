from django.contrib import admin

from .models import BloodRequest


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "blood_group",
        "patient_type",
        "urgency",
        "units_required",
        "units_fulfilled",
        "status",
        "required_at",
        "expires_at",
        "requester",
        "created_at",
    )

    list_filter = (
        "status",
        "urgency",
        "blood_group",
        "patient_type",
        "purpose",
        "contact_type",
    )

    search_fields = (
        "id",
        "patient_name",
        "hospital_name",
        "contact_phone",
        "requester__email",
        "requester__full_name",
    )

    readonly_fields = (
        "requester",
        "contact_verified_at",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    list_per_page = 25