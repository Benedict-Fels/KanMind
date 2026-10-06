from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password


class RegistrationSerializer(serializers.Serializer):
    fullname = serializers.CharField()
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(),
                                    message="This email is already registered."),])
    password = serializers.CharField(
        write_only=True, validators=[validate_password])
    repeated_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        fullname = validated_data["fullname"]
        teile = fullname.split(" ", 1)

        if len(teile) >= 2:
            first_name = teile[0]
            last_name = teile[1]
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
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.check_password(data["password"]):
            raise serializers.ValidationError("Invalid email or password.")

        data["user"] = user
        return data
