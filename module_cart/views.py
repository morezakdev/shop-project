from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.throttling import ScopedRateThrottle
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import Cart, CartItem
from .serializers import CartSerializer, AddCartItemSerializer, UpdateCartItemSerializer
from .utils import release_expired_cart_items, get_cart_available, check_cooldown
from module_catalog.models import ProductVariant
from django.db import transaction


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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cart_add"

    @extend_schema(
        request=AddCartItemSerializer,
        responses={200: CartSerializer, 400: None},
        examples=[
            OpenApiExample(
                "Request example",
                value={"variant_id": 1, "quantity": 2},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant_id = serializer.validated_data["variant_id"]
        quantity = serializer.validated_data["quantity"]

        variant = get_object_or_404(ProductVariant, id=variant_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        release_expired_cart_items(cart)

        cooldown_msg = check_cooldown(request.user, variant)
        if cooldown_msg:
            return Response(
                {"detail": cooldown_msg}, status=status.HTTP_400_BAD_REQUEST
            )

        cart_item = CartItem.objects.filter(cart=cart, variant=variant).first()
        existing_quantity = cart_item.quantity if cart_item else 0


        cap_excluding_self = get_cart_available(variant, exclude_cart_item=cart_item)


        remaining_for_you = cap_excluding_self - existing_quantity

        if quantity > remaining_for_you:
            return Response(
                {"detail": f"موجودی قابل افزودن: {remaining_for_you}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_total = existing_quantity + quantity

        if cart_item:
            cart_item.quantity = new_total
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                cart=cart, variant=variant, quantity=new_total
            )

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
