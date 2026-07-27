from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema
from module_payments.models import Payment
from module_payments.utils import request_payment
from .serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    CheckoutSerializer,
    QuickBuySerializer,
)
from module_cart.models import Cart
from module_cart.utils import release_expired_cart_items, get_quickbuy_available
from module_catalog.models import ProductVariant
from .models import Order, OrderItem, Coupon


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

    @extend_schema(request=CheckoutSerializer, responses={200: None, 400: None})
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address = serializer.validated_data["address"]
        first_name = serializer.validated_data["first_name"]
        last_name = serializer.validated_data["last_name"]
        postal_code = serializer.validated_data["postal_code"]
        coupon_code = serializer.validated_data.get("coupon_code", "").strip()

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

            subtotal = sum(item.variant.price * item.quantity for item in cart_items)

            coupon = None
            discount_amount = 0

            if coupon_code:
                coupon = (
                    Coupon.objects.select_for_update().filter(code=coupon_code).first()
                )
                if not coupon:
                    return Response(
                        {"detail": "کد تخفیف یافت نشد"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not coupon.is_available:
                    return Response(
                        {"detail": "این کد تخفیف دیگر معتبر نیست"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                discount_amount = int(subtotal * coupon.percentage / 100)
                coupon.used_count += 1
                coupon.save()

            total_price = subtotal - discount_amount

            order = Order.objects.create(
                user=request.user,
                address=address,
                first_name=first_name,
                last_name=last_name,
                postal_code=postal_code,
                total_price=total_price,
                coupon=coupon,
                discount_amount=discount_amount,
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

        authority, payment_url = request_payment(order)

        if not authority:
            return Response(
                {"detail": "خطا در اتصال به درگاه پرداخت. لطفاً بعداً تلاش کنید"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Payment.objects.create(
            order=order, authority=authority, amount=order.total_price
        )

        return Response(
            {"payment_url": payment_url, "order_id": order.id},
            status=status.HTTP_200_OK,
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
        first_name = serializer.validated_data["first_name"]
        last_name = serializer.validated_data["last_name"]
        postal_code = serializer.validated_data["postal_code"]

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
                first_name=first_name,
                last_name=last_name,
                postal_code=postal_code,
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
