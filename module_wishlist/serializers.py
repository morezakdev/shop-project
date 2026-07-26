from rest_framework import serializers
from .models import WishlistItem
from module_common.serializers import JalaliModelSerializer
from module_catalog.models import Product


class WishlistItemSerializer(JalaliModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    min_price = serializers.SerializerMethodField()

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_name', 'product_slug', 'product_image', 'min_price', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_min_price(self, obj):
        variant = obj.product.variants.order_by('price').first()
        return variant.price if variant else None


class AddWishlistItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("محصول یافت نشد")
        return value