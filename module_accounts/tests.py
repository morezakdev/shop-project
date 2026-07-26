from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class RegisterFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.phone = "09121234567"
        self.password = "StrongPass123"

    def test_register_creates_inactive_user_and_returns_otp(self):
        response = self.client.post(
            "/api/users/register/",
            {
                "phone_number": self.phone,
                "password": self.password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("otp_code", response.data)

        user = User.objects.get(phone_number=self.phone)
        self.assertFalse(user.is_active)

    def test_verify_otp_activates_user_and_returns_tokens(self):
        register_response = self.client.post(
            "/api/users/register/",
            {
                "phone_number": self.phone,
                "password": self.password,
            },
        )
        otp = register_response.data["otp_code"]

        verify_response = self.client.post(
            "/api/users/verify-otp/",
            {
                "phone_number": self.phone,
                "otp_code": otp,
            },
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", verify_response.data)
        self.assertIn("refresh", verify_response.data)

        user = User.objects.get(phone_number=self.phone)
        self.assertTrue(user.is_active)

    def test_verify_otp_with_wrong_code_fails(self):
        self.client.post(
            "/api/users/register/",
            {
                "phone_number": self.phone,
                "password": self.password,
            },
        )
        response = self.client.post(
            "/api/users/verify-otp/",
            {
                "phone_number": self.phone,
                "otp_code": "000000",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_inactive_user_fails(self):
        self.client.post(
            "/api/users/register/",
            {
                "phone_number": self.phone,
                "password": self.password,
            },
        )
        response = self.client.post(
            "/api/users/login/",
            {
                "phone_number": self.phone,
                "password": self.password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
