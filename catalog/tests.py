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


class ProductSearchTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        groceries = Category.objects.create(name='Groceries')
        drinks = Category.objects.create(name='Drinks', parent=groceries)
        water = Category.objects.create(name='Water', parent=drinks)
        sparkling = Category.objects.create(name='Sparkling Water', parent=water)
        juice = Category.objects.create(name='Juice', parent=drinks)
        fish = Category.objects.create(name='Fish', parent=groceries)
        fillets = Category.objects.create(name='Fillets', parent=fish)
        household = Category.objects.create(name='Household')
        rows = [
            ('still_water', 'Still Water 1.5L', 'DRK-WAT-001', 99, water),
            ('sparkling_water', 'Sparkling Water 1.5L', 'DRK-WAT-002', 129, sparkling),
            ('orange_juice', 'Orange Juice 1L', 'DRK-JUI-001', 349, juice),
            ('sea_bass', 'Sea Bass Fillet', 'FIS-LAV-FIL-001', 1383, fillets),
            ('mackerel', 'Скумрия Филе', 'FIS-SKU-FIL-001', 899, fillets),
            ('dish_soap', 'Dish Soap 500ml', 'HH-SOAP-001', 249, household),
            ('watermelon', 'Watermelon 1kg', 'GRO-WAT-001', 199, groceries),
        ]
        for attr, title, sku, price_cents, category in rows:
            product = Product.objects.create(
                title=title,
                description=f'{title} description',
                sku=sku,
                price_cents=price_cents,
                category=category,
            )
            setattr(cls, attr, product)

    def test_lists_everything_without_filters(self):
        response = self.client.get(reverse('product-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 7)
        self.assertEqual(
            [product['id'] for product in response.data['results']],
            [
                self.still_water.id,
                self.sparkling_water.id,
                self.orange_juice.id,
                self.sea_bass.id,
                self.mackerel.id,
                self.dish_soap.id,
                self.watermelon.id,
            ],
        )

    def test_matches_part_of_title(self):
        response = self.client.get(reverse('product-list'), {'title': 'water'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [product['id'] for product in response.data['results']],
            [self.still_water.id, self.sparkling_water.id, self.watermelon.id],
        )

    def test_matches_title_ignoring_case(self):
        response = self.client.get(reverse('product-list'), {'title': 'скумрия'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([product['id'] for product in response.data['results']], [self.mackerel.id])

    def test_finds_nothing_for_unknown_title(self):
        response = self.client.get(reverse('product-list'), {'title': 'beer'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'count': 0, 'next': None, 'previous': None, 'results': []})

    def test_rejects_short_title(self):
        response = self.client.get(reverse('product-list'), {'title': 'wa'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'title': ['Ensure this field has at least 3 characters.']})

    def test_treats_empty_title_as_absent(self):
        response = self.client.get(reverse('product-list'), {'title': ''})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 7)

    def test_ignores_unknown_parameters(self):
        response = self.client.get(reverse('product-list'), {'colour': 'blue'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 7)


class CategoryCreateTests(APITestCase):
    def test_creates_top_level(self):
        response = self.client.post(reverse('category-list'), {'name': 'Drinks'})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category = Category.objects.get()
        self.assertEqual(
            response.data,
            {
                'id': category.id,
                'name': 'Drinks',
                'parent_id': None,
                'created_at': category.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': category.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )

    def test_creates_child(self):
        drinks = Category.objects.create(name='Drinks')

        response = self.client.post(reverse('category-list'), {'name': 'Water', 'parent_id': drinks.id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        water = Category.objects.get(name='Water')
        self.assertEqual(
            response.data,
            {
                'id': water.id,
                'name': 'Water',
                'parent_id': drinks.id,
                'created_at': water.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': water.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )

    def test_creates_same_name_under_different_parent(self):
        drinks = Category.objects.create(name='Drinks')
        food = Category.objects.create(name='Food')
        Category.objects.create(name='Organic', parent=drinks)

        response = self.client.post(reverse('category-list'), {'name': 'Organic', 'parent_id': food.id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.filter(name='Organic').count(), 2)

    def test_rejects_duplicate_name_under_same_parent(self):
        drinks = Category.objects.create(name='Drinks')
        Category.objects.create(name='Water', parent=drinks)

        response = self.client.post(reverse('category-list'), {'name': 'Water', 'parent_id': drinks.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {'non_field_errors': ['Category name must be unique within its parent.']}
        )
        self.assertEqual(Category.objects.count(), 2)

    def test_rejects_duplicate_top_level_name(self):
        Category.objects.create(name='Drinks')

        response = self.client.post(reverse('category-list'), {'name': 'Drinks'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {'non_field_errors': ['Category name must be unique within its parent.']}
        )
        self.assertEqual(Category.objects.count(), 1)

    def test_rejects_short_name(self):
        response = self.client.post(reverse('category-list'), {'name': 'Dr'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['name'])
        self.assertFalse(Category.objects.exists())

    def test_rejects_missing_name(self):
        response = self.client.post(reverse('category-list'), {'parent_id': None})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['name'])
        self.assertFalse(Category.objects.exists())

    def test_rejects_unknown_parent(self):
        response = self.client.post(reverse('category-list'), {'name': 'Water', 'parent_id': 999})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['parent_id'])
        self.assertFalse(Category.objects.exists())


class CategoryDetailTests(APITestCase):
    def test_found(self):
        drinks = Category.objects.create(name='Drinks')
        water = Category.objects.create(name='Water', parent=drinks)

        response = self.client.get(reverse('category-detail', args=[water.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                'id': water.id,
                'name': 'Water',
                'parent_id': drinks.id,
                'created_at': water.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': water.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )

    def test_not_found(self):
        response = self.client.get(reverse('category-detail', args=[999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CategoryUpdateTests(APITestCase):
    def test_updates(self):
        drinks = Category.objects.create(name='Drinks')
        water = Category.objects.create(name='Water', parent=drinks)

        response = self.client.put(
            reverse('category-detail', args=[water.id]), {'name': 'Still Water', 'parent_id': None}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        water.refresh_from_db()
        self.assertGreater(water.updated_at, water.created_at)
        self.assertEqual(
            response.data,
            {
                'id': water.id,
                'name': 'Still Water',
                'parent_id': None,
                'created_at': water.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': water.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )

    def test_rejects_missing_name(self):
        drinks = Category.objects.create(name='Drinks')

        response = self.client.put(reverse('category-detail', args=[drinks.id]), {'parent_id': None})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['name'])

    def test_not_found(self):
        response = self.client.put(reverse('category-detail', args=[999]), {'name': 'Drinks'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rejects_renaming_to_sibling_name(self):
        drinks = Category.objects.create(name='Drinks')
        Category.objects.create(name='Water', parent=drinks)
        juice = Category.objects.create(name='Juice', parent=drinks)

        response = self.client.patch(reverse('category-detail', args=[juice.id]), {'name': 'Water'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {'non_field_errors': ['Category name must be unique within its parent.']}
        )
        juice.refresh_from_db()
        self.assertEqual(juice.name, 'Juice')

    def test_moves_under_another_parent(self):
        drinks = Category.objects.create(name='Drinks')
        food = Category.objects.create(name='Food')
        water = Category.objects.create(name='Water', parent=drinks)

        response = self.client.patch(reverse('category-detail', args=[water.id]), {'parent_id': food.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        water.refresh_from_db()
        self.assertEqual(water.parent, food)
        self.assertEqual(
            response.data,
            {
                'id': water.id,
                'name': 'Water',
                'parent_id': food.id,
                'created_at': water.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': water.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )

    def test_rejects_self_as_parent(self):
        drinks = Category.objects.create(name='Drinks')

        response = self.client.patch(reverse('category-detail', args=[drinks.id]), {'parent_id': drinks.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'parent_id': ['A category cannot be its own ancestor.']})
        drinks.refresh_from_db()
        self.assertIsNone(drinks.parent)

    def test_rejects_descendant_as_parent(self):
        drinks = Category.objects.create(name='Drinks')
        water = Category.objects.create(name='Water', parent=drinks)
        sparkling = Category.objects.create(name='Sparkling', parent=water)

        response = self.client.patch(
            reverse('category-detail', args=[drinks.id]), {'parent_id': sparkling.id}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'parent_id': ['A category cannot be its own ancestor.']})
        drinks.refresh_from_db()
        self.assertIsNone(drinks.parent)

    def test_patches_partially(self):
        drinks = Category.objects.create(name='Drinks')
        water = Category.objects.create(name='Water', parent=drinks)

        response = self.client.patch(reverse('category-detail', args=[water.id]), {'name': 'Still Water'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        water.refresh_from_db()
        self.assertGreater(water.updated_at, water.created_at)
        self.assertEqual(
            response.data,
            {
                'id': water.id,
                'name': 'Still Water',
                'parent_id': drinks.id,
                'created_at': water.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': water.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )


class CategoryDeleteTests(APITestCase):
    def test_deletes(self):
        drinks = Category.objects.create(name='Drinks')
        water = Category.objects.create(name='Water', parent=drinks)

        response = self.client.delete(reverse('category-detail', args=[water.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=water.id).exists())
        self.assertTrue(Category.objects.filter(pk=drinks.id).exists())

    def test_rejects_category_with_children(self):
        drinks = Category.objects.create(name='Drinks')
        Category.objects.create(name='Water', parent=drinks)

        response = self.client.delete(reverse('category-detail', args=[drinks.id]))

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data, {'detail': 'Category still has products or child categories.'})
        self.assertEqual(Category.objects.count(), 2)

    def test_rejects_category_with_products(self):
        drinks = Category.objects.create(name='Drinks')
        Product.objects.create(title='Still Water 1.5L', sku='DRK-WAT-001', price_cents=99, category=drinks)

        response = self.client.delete(reverse('category-detail', args=[drinks.id]))

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data, {'detail': 'Category still has products or child categories.'})
        self.assertTrue(Category.objects.filter(pk=drinks.id).exists())
        self.assertEqual(Product.objects.count(), 1)

    def test_not_found(self):
        response = self.client.delete(reverse('category-detail', args=[999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProductCreateTests(APITestCase):
    def test_creates(self):
        category = Category.objects.create(name='Drinks')
        payload = {
            'title': 'Still Water 1.5L',
            'description': 'Natural spring water',
            'image_url': 'https://example.com/water.jpg',
            'sku': 'DRK-WAT-001',
            'price_cents': 99,
            'currency': 'EUR',
            'category_id': category.id,
        }

        response = self.client.post(reverse('product-list'), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get()
        self.assertEqual(
            response.data,
            {
                'id': product.id,
                'title': 'Still Water 1.5L',
                'description': 'Natural spring water',
                'image_url': 'https://example.com/water.jpg',
                'sku': 'DRK-WAT-001',
                'price_cents': 99,
                'price_display': '0.99',
                'currency': 'EUR',
                'category_id': category.id,
                'created_at': product.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': product.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )

    def test_creates_without_image_url(self):
        category = Category.objects.create(name='Drinks')
        payload = {
            'title': 'Still Water 1.5L',
            'description': 'Natural spring water',
            'sku': 'DRK-WAT-001',
            'price_cents': 99,
            'currency': 'EUR',
            'category_id': category.id,
        }

        response = self.client.post(reverse('product-list'), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get()
        self.assertEqual(
            response.data,
            {
                'id': product.id,
                'title': 'Still Water 1.5L',
                'description': 'Natural spring water',
                'image_url': None,
                'sku': 'DRK-WAT-001',
                'price_cents': 99,
                'price_display': '0.99',
                'currency': 'EUR',
                'category_id': category.id,
                'created_at': product.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': product.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )

    def test_creates_free_product(self):
        category = Category.objects.create(name='Drinks')
        payload = {
            'title': 'Paper Bag',
            'description': 'Free with every order',
            'image_url': 'https://example.com/bag.jpg',
            'sku': 'PKG-BAG-001',
            'price_cents': 0,
            'currency': 'EUR',
            'category_id': category.id,
        }

        response = self.client.post(reverse('product-list'), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get()
        self.assertEqual(
            response.data,
            {
                'id': product.id,
                'title': 'Paper Bag',
                'description': 'Free with every order',
                'image_url': 'https://example.com/bag.jpg',
                'sku': 'PKG-BAG-001',
                'price_cents': 0,
                'price_display': '0.00',
                'currency': 'EUR',
                'category_id': category.id,
                'created_at': product.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': product.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )

    def test_rejects_short_title(self):
        category = Category.objects.create(name='Drinks')
        payload = {
            'title': 'St',
            'description': 'Natural spring water',
            'image_url': 'https://example.com/water.jpg',
            'sku': 'DRK-WAT-001',
            'price_cents': 99,
            'currency': 'EUR',
            'category_id': category.id,
        }

        response = self.client.post(reverse('product-list'), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['title'])
        self.assertFalse(Product.objects.exists())

    def test_rejects_short_sku(self):
        category = Category.objects.create(name='Drinks')
        payload = {
            'title': 'Still Water 1.5L',
            'description': 'Natural spring water',
            'image_url': 'https://example.com/water.jpg',
            'sku': 'DR',
            'price_cents': 99,
            'currency': 'EUR',
            'category_id': category.id,
        }

        response = self.client.post(reverse('product-list'), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['sku'])
        self.assertFalse(Product.objects.exists())

    def test_rejects_duplicate_sku(self):
        category = Category.objects.create(name='Drinks')
        Product.objects.create(
            title='Still Water 1.5L',
            description='Natural spring water',
            image_url='https://example.com/water.jpg',
            sku='DRK-WAT-001',
            price_cents=99,
            category=category,
        )
        payload = {
            'title': 'Sparkling Water 1.5L',
            'description': 'Carbonated spring water',
            'image_url': 'https://example.com/sparkling.jpg',
            'sku': 'DRK-WAT-001',
            'price_cents': 109,
            'currency': 'EUR',
            'category_id': category.id,
        }

        response = self.client.post(reverse('product-list'), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['sku'])
        self.assertEqual(Product.objects.count(), 1)

    def test_rejects_invalid_image_url(self):
        category = Category.objects.create(name='Drinks')
        payload = {
            'title': 'Still Water 1.5L',
            'description': 'Natural spring water',
            'image_url': 'water.jpg',
            'sku': 'DRK-WAT-001',
            'price_cents': 99,
            'currency': 'EUR',
            'category_id': category.id,
        }

        response = self.client.post(reverse('product-list'), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['image_url'])
        self.assertFalse(Product.objects.exists())

    def test_rejects_negative_price(self):
        category = Category.objects.create(name='Drinks')
        payload = {
            'title': 'Still Water 1.5L',
            'description': 'Natural spring water',
            'image_url': 'https://example.com/water.jpg',
            'sku': 'DRK-WAT-001',
            'price_cents': -1,
            'currency': 'EUR',
            'category_id': category.id,
        }

        response = self.client.post(reverse('product-list'), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['price_cents'])
        self.assertFalse(Product.objects.exists())

    def test_rejects_unknown_currency(self):
        category = Category.objects.create(name='Drinks')
        payload = {
            'title': 'Still Water 1.5L',
            'description': 'Natural spring water',
            'image_url': 'https://example.com/water.jpg',
            'sku': 'DRK-WAT-001',
            'price_cents': 99,
            'currency': 'USD',
            'category_id': category.id,
        }

        response = self.client.post(reverse('product-list'), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['currency'])
        self.assertFalse(Product.objects.exists())

    def test_rejects_missing_required_fields(self):
        response = self.client.post(reverse('product-list'), {'description': 'Natural spring water'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sorted(response.data), ['category_id', 'price_cents', 'sku', 'title'])
        self.assertFalse(Product.objects.exists())

    def test_rejects_unknown_category(self):
        response = self.client.post(
            reverse('product-list'),
            {'title': 'Still Water 1.5L', 'sku': 'DRK-WAT-001', 'price_cents': 99, 'category_id': 999},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ['category_id'])
        self.assertFalse(Product.objects.exists())


class ProductDetailTests(APITestCase):
    def test_found(self):
        category = Category.objects.create(name='Drinks')
        product = Product.objects.create(
            title='Still Water 1.5L',
            description='Natural spring water',
            image_url='https://example.com/water.jpg',
            sku='DRK-WAT-001',
            price_cents=99,
            category=category,
        )

        response = self.client.get(reverse('product-detail', args=[product.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                'id': product.id,
                'title': 'Still Water 1.5L',
                'description': 'Natural spring water',
                'image_url': 'https://example.com/water.jpg',
                'sku': 'DRK-WAT-001',
                'price_cents': 99,
                'price_display': '0.99',
                'currency': 'EUR',
                'category_id': category.id,
                'created_at': product.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': product.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )

    def test_not_found(self):
        response = self.client.get(reverse('product-detail', args=[999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProductUpdateTests(APITestCase):
    def test_updates(self):
        drinks = Category.objects.create(name='Drinks')
        water = Category.objects.create(name='Water', parent=drinks)
        product = Product.objects.create(
            title='Still Water 1.5L',
            description='Natural spring water',
            image_url='https://example.com/water.jpg',
            sku='DRK-WAT-001',
            price_cents=99,
            category=drinks,
        )

        response = self.client.put(
            reverse('product-detail', args=[product.id]),
            {
                'title': 'Still Water 1.5L, 6-pack',
                'description': 'Natural spring water, six bottles',
                'image_url': 'https://example.com/water-6.jpg',
                'sku': 'DRK-WAT-006',
                'price_cents': 549,
                'currency': 'EUR',
                'category_id': water.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertGreater(product.updated_at, product.created_at)
        self.assertEqual(
            response.data,
            {
                'id': product.id,
                'title': 'Still Water 1.5L, 6-pack',
                'description': 'Natural spring water, six bottles',
                'image_url': 'https://example.com/water-6.jpg',
                'sku': 'DRK-WAT-006',
                'price_cents': 549,
                'price_display': '5.49',
                'currency': 'EUR',
                'category_id': water.id,
                'created_at': product.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': product.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )

    def test_rejects_missing_required_fields(self):
        category = Category.objects.create(name='Drinks')
        product = Product.objects.create(
            title='Still Water 1.5L', sku='DRK-WAT-001', price_cents=99, category=category
        )

        response = self.client.put(reverse('product-detail', args=[product.id]), {'title': 'Still Water'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sorted(response.data), ['category_id', 'price_cents', 'sku'])

    def test_not_found(self):
        response = self.client.put(reverse('product-detail', args=[999]), {'title': 'Water'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patches_partially(self):
        category = Category.objects.create(name='Drinks')
        product = Product.objects.create(
            title='Still Water 1.5L',
            description='Natural spring water',
            image_url='https://example.com/water.jpg',
            sku='DRK-WAT-001',
            price_cents=99,
            category=category,
        )

        response = self.client.patch(reverse('product-detail', args=[product.id]), {'price_cents': 129})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertGreater(product.updated_at, product.created_at)
        self.assertEqual(
            response.data,
            {
                'id': product.id,
                'title': 'Still Water 1.5L',
                'description': 'Natural spring water',
                'image_url': 'https://example.com/water.jpg',
                'sku': 'DRK-WAT-001',
                'price_cents': 129,
                'price_display': '1.29',
                'currency': 'EUR',
                'category_id': category.id,
                'created_at': product.created_at.isoformat().replace('+00:00', 'Z'),
                'updated_at': product.updated_at.isoformat().replace('+00:00', 'Z'),
            },
        )


class ProductDeleteTests(APITestCase):
    def test_deletes(self):
        category = Category.objects.create(name='Drinks')
        product = Product.objects.create(
            title='Still Water 1.5L',
            description='Natural spring water',
            image_url='https://example.com/water.jpg',
            sku='DRK-WAT-001',
            price_cents=99,
            category=category,
        )

        response = self.client.delete(reverse('product-detail', args=[product.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=product.id).exists())
        self.assertTrue(Category.objects.filter(pk=category.id).exists())

    def test_not_found(self):
        response = self.client.delete(reverse('product-detail', args=[999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
