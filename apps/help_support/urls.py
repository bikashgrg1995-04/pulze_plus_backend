from django.urls import path

from .views import (
    ContactSupportCreateView,
    FAQListView,
    FeedbackCreateView,
    ReportProblemCreateView,
)


urlpatterns = [
    path(
        "faqs/",
        FAQListView.as_view(),
        name="faq-list",
    ),
    path(
        "contact/",
        ContactSupportCreateView.as_view(),
        name="contact-support",
    ),
    path(
        "report-problem/",
        ReportProblemCreateView.as_view(),
        name="report-problem",
    ),
    path(
        "feedback/",
        FeedbackCreateView.as_view(),
        name="feedback",
    ),

]