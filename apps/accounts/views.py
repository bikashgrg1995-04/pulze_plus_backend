
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Profile

from .serializers import (
    ForgotPasswordSerializer,
    ProfileSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    VerifyPasswordResetSerializer,
)

from .services.email_verification import (
    create_email_verification,
    resend_verification_email,
    send_verification_email,
    verify_email_code,
)

from .services.password_reset import (
    resend_password_reset_code,
    verify_password_reset_code,
    get_valid_password_reset_token,
)

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        with transaction.atomic():
            user = serializer.save()

            code = create_email_verification(
                user,
            )

            send_verification_email(
                user=user,
                code=code,
            )

        return Response(
            {
                "message": (
                    "Account created successfully. "
                    "Please check your email to verify your account."
                ),
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "is_email_verified": (
                        user.is_email_verified
                    ),
                },
            },
            status=status.HTTP_201_CREATED,
        )

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {
                    "message": (
                        "Email and password are required."
                    ),
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request=request,
            username=email,
            password=password,
        )

        if user is None:
            return Response(
                {
                    "message": (
                        "Invalid email or password."
                    ),
                    "errors": {},
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_email_verified:
            return Response(
                {
                    "message": "Please verify your email before logging in.",
                    "errors": {},
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.is_active:
            return Response(
                {
                    "message": (
                        "This account is inactive."
                    ),
                    "errors": {},
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "tokens": {
                    "access": str(
                        refresh.access_token
                    ),
                    "refresh": str(refresh),
                },
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "is_email_verified": (
                        user.is_email_verified
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )

class MeView(APIView):
    def get(self, request):
        user = request.user

        profile = Profile.objects.filter(
            user=user,
        ).first()

        profile_data = None

        if profile is not None:
            profile_data = ProfileSerializer(
                profile,
            ).data

        return Response(
            {
                "message": (
                    "User retrieved successfully."
                ),
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "is_email_verified": (
                        user.is_email_verified
                    ),
                },
                "profile": profile_data,
            },
            status=status.HTTP_200_OK,
        )

class ProfileView(APIView):
    def post(self, request):
        if Profile.objects.filter(
            user=request.user,
        ).exists():
            return Response(
                {
                    "message": (
                        "Profile already exists."
                    ),
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProfileSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save(
            user=request.user,
        )

        return Response(
            {
                "message": (
                    "Profile created successfully."
                ),
                "profile": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        try:
            profile = Profile.objects.get(
                user=request.user,
            )
        except Profile.DoesNotExist:
            return Response(
                {
                    "message": (
                        "Profile does not exist. "
                        "Please complete your profile "
                        "setup first."
                    ),
                    "errors": {},
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        return Response(
            {
                "message": (
                    "Profile updated successfully."
                ),
                "profile": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

class AvatarView(APIView):
    def patch(self, request):
        try:
            profile = Profile.objects.get(
                user=request.user,
            )
        except Profile.DoesNotExist:
            return Response(
                {
                    "message": (
                        "Profile does not exist. "
                        "Please complete your profile "
                        "setup first."
                    ),
                    "errors": {},
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        avatar = request.FILES.get("avatar")

        if avatar is None:
            return Response(
                {
                    "message": "Avatar image is required.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.avatar = avatar
        profile.save(
            update_fields=[
                "avatar",
                "updated_at",
            ],
        )

        return Response(
            {
                "message": "Avatar updated successfully.",
                "avatar": request.build_absolute_uri(
                    profile.avatar.url
                ),
            },
            status=status.HTTP_200_OK,
        )

class DonorStatusView(APIView):
    def patch(self, request):
        try:
            profile = Profile.objects.get(
                user=request.user,
            )
        except Profile.DoesNotExist:
            return Response(
                {
                    "message": (
                        "Profile does not exist. "
                        "Please complete your profile "
                        "setup first."
                    ),
                    "errors": {},
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        is_donor = request.data.get("is_donor")

        if not isinstance(is_donor, bool):
            return Response(
                {
                    "message": "is_donor must be a boolean.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.is_donor = is_donor
        profile.save(
            update_fields=[
                "is_donor",
                "updated_at",
            ],
        )

        return Response(
            {
                "message": "Donor status updated successfully.",
                "is_donor": profile.is_donor,
            },
            status=status.HTTP_200_OK,
        )

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response(
                {
                    "message": "Email and verification code are required.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(
            email__iexact=email.strip()
        ).first()

        if user is None:
            return Response(
                {
                    "message": "Invalid or expired verification code.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_email_verified:
            return Response(
                {
                    "message": "Email is already verified.",
                    "errors": {},
                },
                status=status.HTTP_200_OK,
            )

        if not code.isdigit() or len(code) != 6:
            return Response(
                {
                    "message": "Verification code must be a 6-digit number.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = verify_email_code(
            user=user,
            code=code,
        )

        if result == "invalid_or_expired":
            return Response(
                {
                    "message": "Invalid or expired verification code.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Email verified successfully.",
                "errors": {},
            },
            status=status.HTTP_200_OK,
        )

class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {
                    "message": "Email is required.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(
            email__iexact=email.strip(),
        ).first()

        if user is None:
            return Response(
                {
                    "message": (
                        "If an account exists with "
                        "this email, a verification "
                        "email will be sent."
                    ),
                    "errors": {},
                },
                status=status.HTTP_200_OK,
            )

        result = resend_verification_email(
            user,
        )

        if result == "already_verified":
            return Response(
                {
                    "message": (
                        "Email is already verified."
                    ),
                    "errors": {},
                },
                status=status.HTTP_200_OK,
            )

        if result == "cooldown":
            return Response(
                {
                    "message": (
                        "Please wait before requesting "
                        "another verification email."
                    ),
                    "errors": {},
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return Response(
            {
                "message": (
                    "If your email is not verified, "
                    "a new verification email has been sent."
                ),
                "errors": {},
            },
            status=status.HTTP_200_OK,
        )

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        email = serializer.validated_data["email"]

        user = User.objects.filter(
            email__iexact=email.strip(),
        ).first()

        if user is not None:
            resend_password_reset_code(user)

        return Response(
            {
                "message": (
                    "If an account exists with this email, "
                    "a password reset code has been sent."
                ),
                "errors": {},
            },
            status=status.HTTP_200_OK,
        )

class VerifyPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyPasswordResetSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        user = User.objects.filter(
            email__iexact=email.strip(),
        ).first()

        if user is None:
            return Response(
                {
                    "message": (
                        "Invalid or expired password "
                        "reset code."
                    ),
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_token = verify_password_reset_code(
            user=user,
            code=code,
        )

        if reset_token is None:
            return Response(
                {
                    "message": (
                        "Invalid or expired password "
                        "reset code."
                    ),
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": (
                    "Verification successful."
                ),
                "reset_token": reset_token,
                "errors": {},
            },
            status=status.HTTP_200_OK,
        )

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        reset_token = serializer.validated_data[
            "reset_token"
        ]

        new_password = serializer.validated_data[
            "new_password"
        ]

        token = get_valid_password_reset_token(
            reset_token,
        )

        if token is None:
            return Response(
                {
                    "message": (
                        "Invalid or expired password "
                        "reset token."
                    ),
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = token.user

        with transaction.atomic():
            user.set_password(new_password)

            user.save(
                update_fields=[
                    "password",
                    "updated_at",
                ],
            )

            token.used_at = timezone.now()

            token.save(
                update_fields=[
                    "used_at",
                ],
            )

        return Response(
            {
                "message": (
                    "Password reset successfully. "
                    "Please sign in with your new password."
                ),
                "errors": {},
            },
            status=status.HTTP_200_OK,
        )