from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

EMAIL_CHECK_URL = "/api/email-check/"


class EmailCheckTests(APITestCase):

    def setUp(self):
        self.requester = User.objects.create_user(
            username="kevin@test.de", email="kevin@test.de", password="testpass123"
        )
        self.anna = User.objects.create_user(
            username="anna@test.de",
            email="anna@test.de",
            password="testpass123",
            first_name="Anna",
            last_name="Schmidt",
        )
        token = Token.objects.create(user=self.requester)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_requires_authentication(self):
        self.client.credentials()
        response = self.client.get(EMAIL_CHECK_URL, {"email": "anna@test.de"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_existing_email_returns_user(self):
        response = self.client.get(EMAIL_CHECK_URL, {"email": "anna@test.de"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {"id": self.anna.id, "email": "anna@test.de", "fullname": "Anna Schmidt"}
        self.assertEqual(response.data, expected)

    def test_unknown_email_returns_404(self):
        response = self.client.get(EMAIL_CHECK_URL, {"email": "nobody@test.de"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_email_returns_400(self):
        response = self.client.get(EMAIL_CHECK_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_email_format_returns_400(self):
        response = self.client.get(EMAIL_CHECK_URL, {"email": "not-an-email"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
