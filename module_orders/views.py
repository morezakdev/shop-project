from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema

from .models import Order, OrderItem
from .serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    CheckoutSerializer,
    QuickBuySerializer,
)
from module_cart.models import Cart
from module_cart.utils import release_expired_cart_items, get_quickbuy_available
from module_catalog.models import ProductVariant


class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=CheckoutSerializer, responses={200: OrderDetailSerializer, 400: None}
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address = serializer.validated_data["address"]

        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"detail": "سبد خرید شما خالی است"}, status=status.HTTP_400_BAD_REQUEST
            )

        release_expired_cart_items(cart)
        cart_items = cart.items.select_related("variant", "variant__product").all()

        if not cart_items:
            return Response(
                {"detail": "سبد خرید شما خالی است"}, status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            for item in cart_items:
                variant = (
                    type(item.variant)
                    .objects.select_for_update()
                    .get(id=item.variant_id)
                )
                if item.quantity > variant.stock:
                    return Response(
                        {
                            "detail": f"موجودی «{variant.product.name}» کافی نیست. موجودی فعلی: {variant.stock}"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            total_price = sum(item.variant.price * item.quantity for item in cart_items)
            order = Order.objects.create(
                user=request.user, address=address, total_price=total_price
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    variant=item.variant,
                    product_name=item.variant.product.name,
                    color=item.variant.color,
                    size=item.variant.size,
                    quantity=item.quantity,
                    price_at_purchase=item.variant.price,
                )
                variant = (
                    type(item.variant)
                    .objects.select_for_update()
                    .get(id=item.variant_id)
                )
                variant.stock -= item.quantity
                variant.save()

            cart_items.delete()

        return Response(
            OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED
        )


class QuickBuyView(APIView):
    """خرید فوری بدون رفتن به سبد - از کل موجودی باقی‌مونده استفاده می‌کنه"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=QuickBuySerializer, responses={201: OrderDetailSerializer, 400: None}
    )
    def post(self, request):
        serializer = QuickBuySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant_id = serializer.validated_data["variant_id"]
        quantity = serializer.validated_data["quantity"]
        address = serializer.validated_data["address"]

        with transaction.atomic():
            variant = get_object_or_404(
                ProductVariant.objects.select_for_update(), id=variant_id
            )
            available = get_quickbuy_available(variant)

            if quantity > available:
                return Response(
                    {
                        "detail": f"موجودی کافی برای خرید سریع نیست. حداکثر ممکن: {available}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            order = Order.objects.create(
                user=request.user,
                address=address,
                total_price=variant.price * quantity,
            )
            OrderItem.objects.create(
                order=order,
                variant=variant,
                product_name=variant.product.name,
                color=variant.color,
                size=variant.size,
                quantity=quantity,
                price_at_purchase=variant.price,
            )
            variant.stock -= quantity
            variant.save()

        return Response(
            OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED
        )
