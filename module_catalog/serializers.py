from rest_framework import serializers
from .models import Category, Product, ProductVariant
from module_common.fields import JalaliDateTimeField
from module_cart.utils import get_quickbuy_available


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "is_active"]


class ProductVariantSerializer(serializers.ModelSerializer):
    available_stock = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "color",
            "size",
            "price",
            "available_stock",
            "sku",
            "is_available",
        ]

    def get_available_stock(self, obj):
        return get_quickbuy_available(obj)

    def get_is_available(self, obj):
        return get_quickbuy_available(obj) > 0


class ProductListSerializer(serializers.ModelSerializer):
    """برای نمایش خلاصه توی لیست محصولات"""

    min_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "image", "min_price", "is_active"]

    def get_min_price(self, obj):
        variant = obj.variants.order_by("price").first()
        return variant.price if variant else None


class ProductDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    created_at = JalaliDateTimeField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "categories",
            "variants",
            "is_active",
            "created_at",
        ]


from module_cart.utils import get_quickbuy_available
