from rest_framework import serializers

from catalog.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(
        source='parent', queryset=Category.objects.all(), allow_null=True, default=None
    )

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent_id', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.URLField(allow_null=True, required=False)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category', queryset=Category.objects.all()
    )

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'image_url', 'sku', 'price_cents', 'price_display',
            'currency', 'category_id', 'created_at', 'updated_at',
        ]
