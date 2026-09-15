from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Product


class CategoryListTests(APITestCase):
    def test_empty(self):
        response = self.client.get(reverse('category-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_lists_categories(self):
        drinks = Category.objects.create(name='Drinks')
        water = Category.objects.create(name='Water', parent=drinks)
        juice = Category.objects.create(name='Juice', parent=drinks)
        Category.objects.filter(pk=water.pk).update(name='Still Water')
        water.refresh_from_db()

        response = self.client.get(reverse('category-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            [
                {
                    'id': drinks.id,
                    'name': 'Drinks',
                    'parent_id': None,
                    'created_at': drinks.created_at.isoformat().replace('+00:00', 'Z'),
                    'updated_at': drinks.updated_at.isoformat().replace('+00:00', 'Z'),
                },
                {
                    'id': water.id,
                    'name': 'Still Water',
                    'parent_id': drinks.id,
                    'created_at': water.created_at.isoformat().replace('+00:00', 'Z'),
                    'updated_at': water.updated_at.isoformat().replace('+00:00', 'Z'),
                },
                {
                    'id': juice.id,
                    'name': 'Juice',
                    'parent_id': drinks.id,
                    'created_at': juice.created_at.isoformat().replace('+00:00', 'Z'),
                    'updated_at': juice.updated_at.isoformat().replace('+00:00', 'Z'),
                },
            ],
        )


class ProductListTests(APITestCase):
    def test_empty(self):
        response = self.client.get(reverse('product-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_lists_products(self):
        category = Category.objects.create(name='Drinks')
        skus = ['DRK-WAT-001', 'DRK-WAT-002', 'DRK-JUI-001']
        products = [
            Product.objects.create(title=sku, sku=sku, price_cents=99, category=category)
            for sku in skus
        ]
        Product.objects.filter(pk=products[1].pk).update(price_cents=129)

        response = self.client.get(reverse('product-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([p['id'] for p in response.data], [p.id for p in products])
        self.assertEqual([p['sku'] for p in response.data], skus)
        self.assertEqual(response.data[1]['price_cents'], 129)
        self.assertEqual(response.data[0]['category_id'], category.id)
