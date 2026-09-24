from django.urls import path

from .views import (
    LoginView,
    MeView,
    RegisterView,
    ResendVerificationEmailView,
    VerifyEmailView,
)

urlpatterns = [
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),

    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),

    path(
        "me/",
        MeView.as_view(),
        name="me",
    ),

    path(
        "verify-email/",
        VerifyEmailView.as_view(),
        name="verify-email",
    ),
    
    path(
    "resend-verification/",
    ResendVerificationEmailView.as_view(),
    name="resend-verification",
    ),
]