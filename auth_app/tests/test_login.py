from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class LoginTests(APITestCase):
    url = "/api/login/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="max@test.de",
            email="max@test.de",
            password="Kanmind!2026",
            first_name="Max",
            last_name="Mustermann",
        )

    def test_login_success(self):
        data = {"email": "max@test.de", "password": "Kanmind!2026"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["fullname"], "Max Mustermann")
        self.assertEqual(response.data["email"], "max@test.de")
        self.assertEqual(response.data["user_id"], self.user.id)
        self.assertIn("token", response.data)
        self.assertNotIn("password", response.data)

    def test_login_returns_existing_token(self):
        token = Token.objects.create(user=self.user)
        data = {"email": "max@test.de", "password": "Kanmind!2026"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.data["token"], token.key)

    def test_wrong_password(self):
        data = {"email": "max@test.de", "password": "Falsch!2026"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_email(self):
        data = {"email": "niemand@test.de", "password": "Kanmind!2026"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_error_for_wrong_password_and_unknown_email(self):
        wrong_password = self.client.post(
            self.url,
            {"email": "max@test.de", "password": "Falsch!2026"},
            format="json",
        )
        unknown_email = self.client.post(
            self.url,
            {"email": "niemand@test.de", "password": "Kanmind!2026"},
            format="json",
        )

        self.assertEqual(wrong_password.data, unknown_email.data)

    def test_missing_fields(self):
        for field in ["email", "password"]:
            with self.subTest(field=field):
                data = {"email": "max@test.de", "password": "Kanmind!2026"}
                del data[field]
                response = self.client.post(self.url, data, format="json")
                self.assertEqual(response.status_code,
                                 status.HTTP_400_BAD_REQUEST)
