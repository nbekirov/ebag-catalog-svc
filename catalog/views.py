from rest_framework.generics import ListAPIView

from catalog.models import Category, Product
from catalog.serializers import CategorySerializer, ProductSerializer


class CategoryListAPIView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductListAPIView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
