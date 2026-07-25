from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from module_catalog.models import Category, Product, ProductVariant
from .models import Order

User = get_user_model()


class CheckoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(phone_number='09122222222', password='pass12345')
        self.user.is_active = True
        self.user.save()

        response = self.client.post('/api/users/login/', {
            'phone_number': '09122222222',
            'password': 'pass12345',
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        category = Category.objects.create(name='موبایل')
        product = Product.objects.create(name='گوشی تست')
        product.categories.add(category)
        self.variant = ProductVariant.objects.create(
            product=product, color='مشکی', size='معمولی',
            price=1000000, stock=10, sku='TEST-SKU-002'
        )

        self.client.post('/api/cart/items/', {
            'variant_id': self.variant.id,
            'quantity': 3,
        })

    def test_checkout_creates_order_and_reduces_stock(self):
        response = self.client.post('/api/orders/checkout/', {
            'address': 'تهران، خیابان آزمایشی، پلاک ۱',
            'first_name': 'علی',
            'last_name': 'تستی',
            'postal_code': '1234567890',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_url', response.data)

        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 7)  # 10 - 3 = 7

        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertEqual(order.items.count(), 1)

    def test_checkout_empties_cart(self):
        self.client.post('/api/orders/checkout/', {
            'address': 'تهران، خیابان آزمایشی، پلاک ۱',
            'first_name': 'علی',
            'last_name': 'تستی',
            'postal_code': '1234567890',
        })
        cart_response = self.client.get('/api/cart/')
        self.assertEqual(len(cart_response.data['items']), 0)