from django.contrib.postgres.indexes import GinIndex, OpClass
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.expressions import RawSQL
from django.db.models.functions import Upper


class CategoryQuerySet(models.QuerySet):
    def ancestors_of(self, category_id):
        """The category with this id and every category above it, up to the root."""
        return self.filter(
            id__in=RawSQL(
                """
                WITH RECURSIVE ancestors AS (
                    SELECT id, parent_id FROM catalog_category WHERE id = %s
                  UNION ALL
                    SELECT c.id, c.parent_id FROM catalog_category c
                    JOIN ancestors a ON c.id = a.parent_id
                )
                SELECT id FROM ancestors
                """,
                [category_id],
            )
        )


class ProductQuerySet(models.QuerySet):
    def in_category_tree(self, category_id):
        """Products in the category with this id or in any category below it."""
        return self.filter(
            category_id__in=RawSQL(
                """
                WITH RECURSIVE descendants AS (
                    SELECT id FROM catalog_category WHERE id = %s
                  UNION ALL
                    SELECT c.id FROM catalog_category c
                    JOIN descendants d ON c.parent_id = d.id
                )
                SELECT id FROM descendants
                """,
                [category_id],
            )
        )


class Category(models.Model):
    name = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.PROTECT, related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'Categories'
        constraints = [
            models.UniqueConstraint(
                fields=['parent', 'name'],
                nulls_distinct=False,
                name='catalog_category_name_unique_per_parent',
                violation_error_message='Category name must be unique within its parent.',
            ),
        ]

    def __str__(self):
        return self.name

    def is_ancestor_of(self, other):
        return Category.objects.ancestors_of(other.id).filter(pk=self.pk).exists()


class Product(models.Model):
    class Currency(models.TextChoices):
        EUR = 'EUR', 'Euro'

    title = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    description = models.TextField(default='', blank=True)
    image_url = models.TextField(null=True, blank=True)
    sku = models.CharField(max_length=255, unique=True, validators=[MinLengthValidator(3)])
    price_cents = models.PositiveIntegerField(db_index=True)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EUR)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ['id']
        indexes = [
            GinIndex(
                OpClass(Upper('title'), name='gin_trgm_ops'),
                name='catalog_product_title_trgm',
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def price_display(self):
        units, cents = divmod(self.price_cents, 100)
        return f'{units}.{cents:02d}'
