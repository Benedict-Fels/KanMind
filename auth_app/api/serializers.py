"""Serializers for user registration and login."""

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class RegistrationSerializer(serializers.Serializer):
    """Validate registration data and create a new user."""

    fullname = serializers.CharField()
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(),
                                    message="This email is "
                                    "already registered."),])
    password = serializers.CharField(
        write_only=True, validators=[validate_password])
    repeated_password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Make sure both passwords match."""
        if data["password"] != data["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        """Split the full name and create the user (email as username)."""
        fullname = validated_data["fullname"]
        parts = fullname.split(" ", 1)

        if len(parts) >= 2:
            first_name = parts[0]
            last_name = parts[1]
        else:
            first_name = fullname
            last_name = ""

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Check email and password and return the matching user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Find the user by email and check the password."""
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.check_password(data["password"]):
            raise serializers.ValidationError("Invalid email or password.")

        data["user"] = user
        return data
