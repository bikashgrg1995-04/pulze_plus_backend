
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-date_joined",)

    list_display = (
        "full_name",
        "email",
        "is_email_verified",
        "is_active",
        "is_staff",
        "date_joined",
    )

    search_fields = (
        "full_name",
        "email",
    )

    readonly_fields = (
        "last_login",
        "date_joined",
        "updated_at",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Personal information",
            {
                "fields": (
                    "full_name",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "is_email_verified",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "phone_number",
        "gender",
        "blood_type",
        "date_of_birth",
        "city",
        "created_at",
    )

    search_fields = (
        "user__full_name",
        "user__email",
        "phone_number",
        "city",
        "address",
    )

    list_filter = (
        "gender",
        "blood_type",
        "city",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )
