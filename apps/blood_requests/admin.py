from django.contrib import admin

from .models import BloodRequest, BloodRequestResponse


class BloodRequestResponseInline(admin.TabularInline):
    model = BloodRequestResponse
    extra = 0

    fields = (
        "donor",
        "status",
        "units_completed",
        "created_at",
        "updated_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "blood_group",
        "request_type",
        "target_donor",
        "patient_type",
        "urgency",
        "units_required",
        "units_fulfilled",
        "units_remaining_display",
        "status",
        "required_at",
        "expires_at",
        "requester",
        "created_at",
    )

    list_filter = (
        "status",
        "request_type",
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
        "target_donor__user__email",
        "target_donor__user__full_name",
    )

    readonly_fields = (
        "requester",
        "contact_verified_at",
        "created_at",
        "updated_at",
        "units_remaining_display",
    )

    fieldsets = (
        (
            "Request Information",
            {
                "fields": (
                    "requester",
                    "request_type",
                    "target_donor",
                    "status",
                ),
            },
        ),
        (
            "Patient Information",
            {
                "fields": (
                    "patient_type",
                    "patient_name",
                    "requester_relationship",
                    "other_relationship",
                ),
            },
        ),
        (
            "Blood Requirement",
            {
                "fields": (
                    "blood_group",
                    "units_required",
                    "units_fulfilled",
                    "units_remaining_display",
                    "urgency",
                    "required_at",
                    "expires_at",
                ),
            },
        ),
        (
            "Hospital & Location",
            {
                "fields": (
                    "hospital_name",
                    "location",
                ),
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "contact_type",
                    "contact_phone",
                    "contact_verified_at",
                ),
            },
        ),
        (
            "Additional Information",
            {
                "fields": (
                    "purpose",
                    "purpose_other",
                    "note",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    inlines = (
        BloodRequestResponseInline,
    )

    ordering = ("-created_at",)

    list_per_page = 25

    @admin.display(
        description="Units Remaining",
        ordering="units_fulfilled",
    )
    def units_remaining_display(self, obj):
        return obj.units_remaining


@admin.register(BloodRequestResponse)
class BloodRequestResponseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "blood_request",
        "donor",
        "status",
        "units_completed",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "blood_request__id",
        "blood_request__patient_name",
        "blood_request__hospital_name",
        "donor__user__email",
        "donor__user__full_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    list_per_page = 25

