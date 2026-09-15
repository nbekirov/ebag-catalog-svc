from django.core.validators import MinLengthValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    class Currency(models.TextChoices):
        EUR = 'EUR', 'Euro'

    title = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    description = models.TextField(default='', blank=True)
    image_url = models.TextField(null=True, blank=True)
    sku = models.CharField(max_length=255, unique=True, validators=[MinLengthValidator(3)])
    price_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EUR)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
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
