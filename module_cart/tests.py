from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from module_catalog.models import Category, Product, ProductVariant

User = get_user_model()


class CartReservationCapTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # ساخت کاربر فعال و لاگین
        self.user = User.objects.create_user(phone_number='09121111111', password='pass12345')
        self.user.is_active = True
        self.user.save()

        response = self.client.post('/api/users/login/', {
            'phone_number': '09121111111',
            'password': 'pass12345',
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # ساخت یه محصول با موجودی ۱۰ (سقف رزرو = ۷)
        category = Category.objects.create(name='موبایل')
        product = Product.objects.create(name='گوشی تست')
        product.categories.add(category)
        self.variant = ProductVariant.objects.create(
            product=product, color='مشکی', size='معمولی',
            price=1000000, stock=10, sku='TEST-SKU-001'
        )

    def test_can_reserve_up_to_cap(self):
        response = self.client.post('/api/cart/items/', {
            'variant_id': self.variant.id,
            'quantity': 7,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_exceed_cap(self):
        self.client.post('/api/cart/items/', {
            'variant_id': self.variant.id,
            'quantity': 7,
        })
        response = self.client.post('/api/cart/items/', {
            'variant_id': self.variant.id,
            'quantity': 1,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stock_not_reduced_when_adding_to_cart(self):
        self.client.post('/api/cart/items/', {
            'variant_id': self.variant.id,
            'quantity': 5,
        })
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 10)  # موجودی واقعی نباید تغییر کنه