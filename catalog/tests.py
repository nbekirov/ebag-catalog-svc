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
        rows = [
            {'title': 'Still Water 1.5L', 'sku': 'DRK-WAT-001', 'price_cents': 99},
            {'title': 'Sparkling Water 1.5L', 'sku': 'DRK-WAT-002', 'price_cents': 1000},
            {'title': 'Orange Juice 1L', 'sku': 'DRK-JUI-001', 'price_cents': 1383},
        ]
        products = [
            Product.objects.create(
                description=f'{row["title"]} description',
                image_url=f'https://example.com/{row["sku"]}.jpg',
                category=category,
                **row,
            )
            for row in rows
        ]
        Product.objects.filter(pk=products[1].pk).update(price_cents=0)
        products[1].refresh_from_db()

        response = self.client.get(reverse('product-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                'count': 3,
                'next': None,
                'previous': None,
                'results': [
                    {
                        'id': products[0].id,
                        'title': 'Still Water 1.5L',
                        'description': 'Still Water 1.5L description',
                        'image_url': 'https://example.com/DRK-WAT-001.jpg',
                        'sku': 'DRK-WAT-001',
                        'price_cents': 99,
                        'price_display': '0.99',
                        'currency': 'EUR',
                        'category_id': category.id,
                        'created_at': products[0].created_at.isoformat().replace('+00:00', 'Z'),
                        'updated_at': products[0].updated_at.isoformat().replace('+00:00', 'Z'),
                    },
                    {
                        'id': products[1].id,
                        'title': 'Sparkling Water 1.5L',
                        'description': 'Sparkling Water 1.5L description',
                        'image_url': 'https://example.com/DRK-WAT-002.jpg',
                        'sku': 'DRK-WAT-002',
                        'price_cents': 0,
                        'price_display': '0.00',
                        'currency': 'EUR',
                        'category_id': category.id,
                        'created_at': products[1].created_at.isoformat().replace('+00:00', 'Z'),
                        'updated_at': products[1].updated_at.isoformat().replace('+00:00', 'Z'),
                    },
                    {
                        'id': products[2].id,
                        'title': 'Orange Juice 1L',
                        'description': 'Orange Juice 1L description',
                        'image_url': 'https://example.com/DRK-JUI-001.jpg',
                        'sku': 'DRK-JUI-001',
                        'price_cents': 1383,
                        'price_display': '13.83',
                        'currency': 'EUR',
                        'category_id': category.id,
                        'created_at': products[2].created_at.isoformat().replace('+00:00', 'Z'),
                        'updated_at': products[2].updated_at.isoformat().replace('+00:00', 'Z'),
                    },
                ],
            },
        )

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
