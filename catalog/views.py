from rest_framework.generics import ListAPIView

from catalog.models import Category
from catalog.serializers import CategorySerializer


class CategoryListAPIView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
