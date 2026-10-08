"""API views for registration and login."""

from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer


class RegistrationView(APIView):
    """Register a new user and return a token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Create the user and respond with token and user data."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "fullname": user.get_full_name(),
                "email": user.email,
                "user_id": user.id,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Log in with email and password and return a token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Check the credentials and respond with token and user data."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "fullname": user.get_full_name(),
                "email": user.email,
                "user_id": user.id,
            },
            status=status.HTTP_200_OK,
        )
