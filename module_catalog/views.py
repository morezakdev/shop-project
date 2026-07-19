from rest_framework import generics, permissions
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
)
from django.db.models import Min
from rest_framework import generics, permissions, filters


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "min_price"]
    ordering = ["-created_at"]  

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).annotate(
            min_price=Min("variants__price")
        )
        category_slug = self.request.query_params.get("category")
        if category_slug:
            qs = qs.filter(categories__slug=category_slug)
        return qs


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
