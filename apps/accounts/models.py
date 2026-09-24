from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(
        max_length=150,
    )

    email = models.EmailField(
        unique=True,
    )

    phone_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
    )

    is_email_verified = models.BooleanField(
        default=False,
    )

    is_phone_verified = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    date_joined = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.email