from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema
from module_cart.utils import release_expired_cart_items
from .models import Order, OrderItem
from .serializers import OrderListSerializer, OrderDetailSerializer, CheckoutSerializer
from module_cart.models import Cart


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
            total_price = sum(item.variant.price * item.quantity for item in cart_items)

            order = Order.objects.create(
                user=request.user,
                address=address,
                total_price=total_price,
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
            cart_items.delete()

        return Response(
            OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED
        )
