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

    def test_not_paginated(self):
        for i in range(25):
            Category.objects.create(name=f'Category {i}')

        response = self.client.get(reverse('category-list'), {'limit': 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 25)


class ProductListTests(APITestCase):
    def test_empty(self):
        response = self.client.get(reverse('product-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'count': 0, 'next': None, 'previous': None, 'results': []})

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
        self.assertEqual(response.data['count'], 3)
        results = response.data['results']
        self.assertEqual([p['id'] for p in results], [p.id for p in products])
        self.assertEqual([p['sku'] for p in results], skus)
        self.assertEqual(results[1]['price_cents'], 129)
        self.assertEqual(results[0]['category_id'], category.id)

    def test_paginated(self):
        category = Category.objects.create(name='Drinks')
        products = [
            Product.objects.create(title=f'P{i}', sku=f'SKU-{i}', price_cents=99, category=category)
            for i in range(5)
        ]

        ids = [p.id for p in products]

        def page(**params):
            response = self.client.get(reverse('product-list'), params)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['count'], 5)
            return response.data

        # first page
        data = page(limit=2)
        self.assertEqual([p['id'] for p in data['results']], ids[0:2])
        self.assertIsNone(data['previous'])
        self.assertIn('limit=2&offset=2', data['next'])

        # middle page
        data = page(limit=2, offset=2)
        self.assertEqual([p['id'] for p in data['results']], ids[2:4])
        self.assertIn('limit=2', data['previous'])
        self.assertIn('limit=2&offset=4', data['next'])

        # last, partial page
        data = page(limit=2, offset=4)
        self.assertEqual([p['id'] for p in data['results']], ids[4:5])
        self.assertIn('limit=2&offset=2', data['previous'])
        self.assertIsNone(data['next'])

        # beyond the end
        data = page(limit=2, offset=6)
        self.assertEqual(data['results'], [])
        self.assertIsNone(data['next'])

        # limit larger than the collection
        data = page(limit=10)
        self.assertEqual([p['id'] for p in data['results']], ids)
        self.assertIsNone(data['previous'])
        self.assertIsNone(data['next'])
