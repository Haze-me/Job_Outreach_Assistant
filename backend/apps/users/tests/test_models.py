"""Tests for the custom user model and its manager."""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestUserManager:
    def test_create_user_normalises_and_hashes(self):
        user = User.objects.create_user(email="  Jane.Doe@Example.COM ", password="s3cret-pass")

        assert user.email == "jane.doe@example.com"
        assert isinstance(user.pk, uuid.UUID)
        # The raw password must never be stored.
        assert user.password != "s3cret-pass"
        assert user.check_password("s3cret-pass")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match="email address is required"):
            User.objects.create_user(email="", password="s3cret-pass")

    def test_create_user_rejects_invalid_email(self):
        with pytest.raises(ValidationError):
            User.objects.create_user(email="not-an-email", password="s3cret-pass")

    def test_email_is_unique_case_insensitively(self):
        User.objects.create_user(email="dup@example.com", password="s3cret-pass")

        with pytest.raises((ValidationError, IntegrityError)):
            User.objects.create_user(email="DUP@example.com", password="s3cret-pass")

    def test_create_superuser(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="s3cret-pass")

        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_create_superuser_rejects_non_staff(self):
        with pytest.raises(ValueError, match="is_staff=True"):
            User.objects.create_superuser(
                email="admin@example.com", password="s3cret-pass", is_staff=False
            )


class TestUserModel:
    def test_string_representation_is_email(self):
        user = User.objects.create_user(email="user@example.com", password="s3cret-pass")

        assert str(user) == "user@example.com"

    def test_name_helpers(self):
        user = User.objects.create_user(
            email="user@example.com",
            password="s3cret-pass",
            first_name="Ada",
            last_name="Lovelace",
        )

        assert user.full_name == "Ada Lovelace"
        assert user.get_full_name() == "Ada Lovelace"
        assert user.get_short_name() == "Ada"

    def test_name_helpers_fall_back_to_email(self):
        user = User.objects.create_user(email="user@example.com", password="s3cret-pass")

        assert user.full_name == ""
        assert user.get_full_name() == "user@example.com"
        assert user.get_short_name() == "user"

    def test_username_field_is_email(self):
        assert User.USERNAME_FIELD == "email"
        assert User.REQUIRED_FIELDS == []
