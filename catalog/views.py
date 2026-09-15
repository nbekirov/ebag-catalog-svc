from django.db.models import ProtectedError
from rest_framework.exceptions import APIException
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from catalog.models import Category, Product
from catalog.serializers import CategorySerializer, ProductSearchSerializer, ProductSerializer


class CategoryInUse(APIException):
    status_code = 409
    default_detail = 'Category still has products or child categories.'


class CategoryListAPIView(ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class CategoryDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise CategoryInUse


class ProductListAPIView(ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def filter_queryset(self, queryset):
        search = ProductSearchSerializer(data=self.request.query_params)
        search.is_valid(raise_exception=True)
        params = search.validated_data
        if 'title' in params:
            queryset = queryset.filter(title__icontains=params['title'])
        return queryset


class ProductDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
