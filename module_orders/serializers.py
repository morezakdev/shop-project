from rest_framework import serializers
from .models import Order, OrderItem
from module_common.fields import JalaliDateTimeField


class OrderItemSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(
        max_digits=14, decimal_places=0, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "color",
            "size",
            "quantity",
            "price_at_purchase",
            "total_price",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """برای لیست سفارش‌ها - خلاصه"""

    created_at = JalaliDateTimeField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "status_display", "total_price", "created_at"]


class OrderDetailSerializer(serializers.ModelSerializer):
    """برای جزئیات یک سفارش - کامل با آیتم‌ها"""

    items = OrderItemSerializer(many=True, read_only=True)
    created_at = JalaliDateTimeField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "first_name",
            "last_name",
            "postal_code",
            "address",
            "status",
            "status_display",
            "total_price",
            "items",
            "created_at",
        ]


class CheckoutSerializer(serializers.Serializer):
    address = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    postal_code = serializers.CharField()


class QuickBuySerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    address = serializers.CharField(min_length=10, max_length=500)
