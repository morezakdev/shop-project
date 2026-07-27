from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status

from module_catalog.models import Category, Product
from .models import WishlistItem

User = get_user_model()


class WishlistTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

        self.user = User.objects.create_user(phone_number='09125555555', password='pass12345')
        self.user.is_active = True
        self.user.save()

        response = self.client.post('/api/users/login/', {
            'phone_number': '09125555555',
            'password': 'pass12345',
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        category = Category.objects.create(name='موبایل')
        self.product = Product.objects.create(name='گوشی تست')
        self.product.categories.add(category)

    def test_add_product_to_wishlist(self):
        response = self.client.post('/api/wishlist/add/', {'product_id': self.product.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(WishlistItem.objects.filter(user=self.user, product=self.product).exists())

    def test_adding_same_product_twice_fails(self):
        self.client.post('/api/wishlist/add/', {'product_id': self.product.id})
        response = self.client.post('/api/wishlist/add/', {'product_id': self.product.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_wishlist_items(self):
        self.client.post('/api/wishlist/add/', {'product_id': self.product.id})
        response = self.client.get('/api/wishlist/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_remove_wishlist_item(self):
        self.client.post('/api/wishlist/add/', {'product_id': self.product.id})
        item = WishlistItem.objects.get(user=self.user, product=self.product)

        response = self.client.delete(f'/api/wishlist/{item.id}/remove/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WishlistItem.objects.filter(id=item.id).exists())

    def test_cannot_remove_other_users_wishlist_item(self):
        other_user = User.objects.create_user(phone_number='09126666666', password='pass12345')
        other_user.is_active = True
        other_user.save()
        other_item = WishlistItem.objects.create(user=other_user, product=self.product)

        response = self.client.delete(f'/api/wishlist/{other_item.id}/remove/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)