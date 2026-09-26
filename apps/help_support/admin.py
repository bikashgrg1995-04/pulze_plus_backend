from django.contrib import admin

from .models import FAQ, SupportRequest


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "category",
        "order",
        "is_active",
        "updated_at",
    )
    list_filter = (
        "category",
        "is_active",
    )
    search_fields = (
        "question",
        "answer",
    )
    ordering = (
        "order",
        "-created_at",
    )


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "request_type",
        "subject",
        "status",
        "created_at",
    )
    list_filter = (
        "request_type",
        "status",
    )
    search_fields = (
        "subject",
        "message",
        "user__email",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "user",
        "request_type",
        "subject",
        "message",
        "created_at",
        "updated_at",
    )
