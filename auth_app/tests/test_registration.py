from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class RegistrationTests(APITestCase):
    url = "/api/registration/"

    def valid_data(self, **changes):
        data = {
            "fullname": "Max Mustermann",
            "email": "max@test.de",
            "password": "Kanmind!2026",
            "repeated_password": "Kanmind!2026",
        }
        data.update(changes)
        return data

    def test_registration_success(self):
        response = self.client.post(self.url, self.valid_data(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["fullname"], "Max Mustermann")
        self.assertNotIn("password", response.data)
        self.assertTrue(User.objects.filter(email="max@test.de").exists())

    def test_duplicate_email(self):
        self.client.post(self.url, self.valid_data(), format="json")
        response = self.client.post(self.url, self.valid_data(), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_password_mismatch(self):
        data = self.valid_data(repeated_password="Anders!2026")
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("repeated_password", response.data)

    def test_invalid_emails(self):
        for email in ["keine-email", "max@", "@test.de", ""]:
            with self.subTest(email=email):
                data = self.valid_data(email=email)
                response = self.client.post(self.url, data, format="json")
                self.assertEqual(response.status_code,
                                 status.HTTP_400_BAD_REQUEST)

    def test_missing_fields(self):
        for field in ["fullname", "email", "password", "repeated_password"]:
            with self.subTest(field=field):
                data = self.valid_data()
                del data[field]
                response = self.client.post(self.url, data, format="json")
                self.assertEqual(response.status_code,
                                 status.HTTP_400_BAD_REQUEST)
