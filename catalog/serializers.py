from rest_framework import serializers

from catalog.models import Category


class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(
        source='parent', queryset=Category.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent_id', 'created_at', 'updated_at']
