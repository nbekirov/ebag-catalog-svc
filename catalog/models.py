from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.expressions import RawSQL


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
    price_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EUR)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.title

    @property
    def price_display(self):
        units, cents = divmod(self.price_cents, 100)
        return f'{units}.{cents:02d}'
