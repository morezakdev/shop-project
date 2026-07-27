from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from .models import Category, Product, ProductVariant


class ProductListTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.category = Category.objects.create(name='موبایل')
        self.product1 = Product.objects.create(name='آیفون ۱۵')
        self.product1.categories.add(self.category)
        ProductVariant.objects.create(
            product=self.product1, color='مشکی', size='معمولی',
            price=50000000, stock=5, sku='IPHONE-15-BLACK'
        )

        self.product2 = Product.objects.create(name='سامسونگ گلکسی')
        self.product2.categories.add(self.category)
        ProductVariant.objects.create(
            product=self.product2, color='آبی', size='معمولی',
            price=30000000, stock=3, sku='SAMSUNG-S24-BLUE'
        )

    def test_list_products_returns_all_active(self):
        response = self.client.get('/api/catalog/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_category(self):
        response = self.client.get(f'/api/catalog/products/?category={self.category.slug}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_search_by_name(self):
        response = self.client.get('/api/catalog/products/?search=آیفون')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'آیفون ۱۵')

    def test_ordering_by_price(self):
        response = self.client.get('/api/catalog/products/?ordering=min_price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # سامسونگ (۳۰ میلیون) باید قبل از آیفون (۵۰ میلیون) بیاد
        self.assertEqual(response.data['results'][0]['name'], 'سامسونگ گلکسی')

    def test_product_detail_by_slug(self):
        response = self.client.get(f'/api/catalog/products/{self.product1.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'آیفون ۱۵')
        self.assertIn('variants', response.data)