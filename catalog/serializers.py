from rest_framework import serializers

from catalog.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(
        source='parent', queryset=Category.objects.all(), allow_null=True, default=None
    )

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent_id', 'created_at', 'updated_at']

    def validate_parent_id(self, parent):
        if parent is not None and self.instance is not None and self.instance.is_ancestor_of(parent):
            raise serializers.ValidationError('A category cannot be its own ancestor.')
        return parent


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


class ProductSearchSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, min_length=3)
    sku = serializers.CharField(required=False)
