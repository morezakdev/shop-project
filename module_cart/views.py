from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import Cart, CartItem
from .serializers import CartSerializer, AddCartItemSerializer, UpdateCartItemSerializer
from .utils import release_expired_cart_items
from module_catalog.models import ProductVariant


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CartSerializer})
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        release_expired_cart_items(cart)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=AddCartItemSerializer,
        responses={200: CartSerializer, 400: None},
        examples=[
            OpenApiExample(
                "Request example",
                value={"variant_id": 1, "quantity": 2},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant_id = serializer.validated_data["variant_id"]
        quantity = serializer.validated_data["quantity"]

        cart, created = Cart.objects.get_or_create(user=request.user)
        release_expired_cart_items(cart)

        with transaction.atomic():
            variant = get_object_or_404(
                ProductVariant.objects.select_for_update(), id=variant_id
            )

            if quantity > variant.stock:
                return Response(
                    {"detail": f"موجودی کافی نیست. موجودی فعلی: {variant.stock}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart, variant=variant, defaults={"quantity": 0}
            )

            # رزرو: موجودی رو بلافاصله کم می‌کنیم
            variant.stock -= quantity
            variant.save()

            cart_item.quantity += quantity
            cart_item.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class UpdateCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=UpdateCartItemSerializer,
        responses={200: CartSerializer, 400: None},
        examples=[
            OpenApiExample("Request example", value={"quantity": 5}, request_only=True),
        ],
    )
    def patch(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        release_expired_cart_items(cart_item.cart)

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            variant = (
                type(cart_item.variant)
                .objects.select_for_update()
                .get(id=cart_item.variant_id)
            )
            diff = new_quantity - cart_item.quantity

            if diff > 0 and diff > variant.stock:
                return Response(
                    {"detail": f"موجودی کافی نیست. موجودی فعلی: {variant.stock}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # diff مثبت یعنی نیاز به رزرو بیشتر (کم کردن از موجودی)
            # diff منفی یعنی آزادسازی بخشی از رزرو قبلی (برگردوندن به موجودی)
            variant.stock -= diff
            variant.save()

            cart_item.quantity = new_quantity
            cart_item.save()

        return Response(CartSerializer(cart_item.cart).data, status=status.HTTP_200_OK)


class RemoveCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CartSerializer})
    def delete(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        release_expired_cart_items(cart_item.cart)
        cart = cart_item.cart

        with transaction.atomic():
            variant = (
                type(cart_item.variant)
                .objects.select_for_update()
                .get(id=cart_item.variant_id)
            )
            variant.stock += cart_item.quantity
            variant.save()
            cart_item.delete()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
