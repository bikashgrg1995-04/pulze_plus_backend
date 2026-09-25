from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    MeView,
    ProfileView,
    AvatarView,
    DonorStatusView,
    RegisterView,
    ResendVerificationEmailView,
    VerifyEmailView,
    ForgotPasswordView,
    VerifyPasswordResetView,
    ResetPasswordView,
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
        "profile/avatar/",
        AvatarView.as_view(),
        name="profile-avatar",
    ),

    path(
        "profile/donor/",
        DonorStatusView.as_view(),
        name="profile-donor",
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

    path("profile/", ProfileView.as_view(), name="profile"),

    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),

    path(
        "forgot-password/",
        ForgotPasswordView.as_view(),
        name="forgot-password",
    ),
    path(
        "verify-password-reset/",
        VerifyPasswordResetView.as_view(),
        name="verify-password-reset",
    ),
    path(
        "reset-password/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
]