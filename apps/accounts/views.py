from django.db import transaction

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Profile

from .serializers import (
    ProfileSerializer,
    RegisterSerializer,
)

from .services.email_verification import (
    create_email_verification,
    resend_verification_email,
    send_verification_email,
    verify_email_token,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()

            raw_token = create_email_verification(user)

            send_verification_email(
                user=user,
                raw_token=raw_token,
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
                    "phone_number": user.phone_number,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified,
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
                    "message": "Email and password are required.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth import authenticate

        user = authenticate(
            request=request,
            username=email,
            password=password,
        )

        if user is None:
            return Response(
                {
                    "message": "Invalid email or password.",
                    "errors": {},
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {
                    "message": "This account is inactive.",
                    "errors": {},
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified,
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
            profile_data = ProfileSerializer(profile).data

        return Response(
            {
                "message": "User retrieved successfully.",
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified,
                },
                "profile": profile_data,
            },
            status=status.HTTP_200_OK,
        )

class ProfileView(APIView):
    def post(self, request):
        if Profile.objects.filter(user=request.user).exists():
            return Response(
                {
                    "message": "Profile already exists.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response(
            {
                "message": "Profile created successfully.",
                "profile": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response(
                {
                    "message": (
                        "Profile does not exist. "
                        "Please complete your profile setup first."
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

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Profile updated successfully.",
                "profile": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        raw_token = request.query_params.get("token")

        if not raw_token:
            return Response(
                {
                    "message": "Invalid or expired verification link.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = verify_email_token(raw_token)

        if result == "invalid_or_expired":
            return Response(
                {
                    "message": "Invalid or expired verification link.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if result == "already_verified":
            return Response(
                {
                    "message": "Email is already verified.",
                    "errors": {},
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "message": "Email verified successfully.",
                "errors": {},
            },
            status=status.HTTP_200_OK,
        )


from django.contrib.auth import get_user_model

User = get_user_model()

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
                        "If an account exists with this email, "
                        "a verification email will be sent."
                    ),
                    "errors": {},
                },
                status=status.HTTP_200_OK,
            )

        result = resend_verification_email(user)

        if result == "already_verified":
            return Response(
                {
                    "message": "Email is already verified.",
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

