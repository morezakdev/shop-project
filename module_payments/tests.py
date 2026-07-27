from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status

from module_catalog.models import Category, Product, ProductVariant
from module_orders.models import Order
from .models import Payment

User = get_user_model()


class PaymentCallbackTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

        self.user = User.objects.create_user(
            phone_number="09123333333", password="pass12345"
        )
        self.user.is_active = True
        self.user.save()

        category = Category.objects.create(name="موبایل")
        product = Product.objects.create(name="گوشی تست")
        product.categories.add(category)
        variant = ProductVariant.objects.create(
            product=product,
            color="مشکی",
            size="معمولی",
            price=1000000,
            stock=10,
            sku="TEST-SKU-PAY-001",
        )

        self.order = Order.objects.create(
            user=self.user,
            address="تهران، خیابان آزمایشی",
            first_name="محمدحسین",
            last_name="احمدی",
            postal_code="1234567890",
            total_price=1000000,
        )

        self.payment = Payment.objects.create(
            order=self.order,
            authority="S00000000000000000000000000012345678",
            amount=1000000,
        )

    def test_callback_without_authority_fails(self):
        response = self.client.get("/api/payments/callback/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_callback_with_unknown_authority_returns_404(self):
        response = self.client.get(
            "/api/payments/callback/",
            {
                "Authority": "UNKNOWN-AUTHORITY",
                "Status": "OK",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_callback_with_status_not_ok_marks_payment_failed(self):
        response = self.client.get(
            "/api/payments/callback/",
            {
                "Authority": self.payment.authority,
                "Status": "NOK",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_FAILED)

    @patch("module_payments.views.verify_payment")
    def test_callback_success_marks_order_paid(self, mock_verify_payment):
        mock_verify_payment.return_value = (True, "REF123456")

        response = self.client.get(
            "/api/payments/callback/",
            {
                "Authority": self.payment.authority,
                "Status": "OK",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ref_id"], "REF123456")

        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(self.payment.ref_id, "REF123456")
        self.assertEqual(self.order.status, Order.STATUS_PAID)

    @patch("module_payments.views.verify_payment")
    def test_callback_verify_failure_marks_payment_failed(self, mock_verify_payment):
        mock_verify_payment.return_value = (False, None)

        response = self.client.get(
            "/api/payments/callback/",
            {
                "Authority": self.payment.authority,
                "Status": "OK",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_FAILED)

    @patch("module_payments.views.verify_payment")
    def test_callback_is_idempotent_for_success(self, mock_verify_payment):
        mock_verify_payment.return_value = (True, "REF123456")

        self.client.get(
            "/api/payments/callback/",
            {
                "Authority": self.payment.authority,
                "Status": "OK",
            },
        )
        response = self.client.get(
            "/api/payments/callback/",
            {
                "Authority": self.payment.authority,
                "Status": "OK",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_verify_payment.call_count, 1)  # فقط یه‌بار صدا زده شده
