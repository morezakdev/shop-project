from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import WishlistItem
from .serializers import WishlistItemSerializer, AddWishlistItemSerializer
from module_catalog.models import Product


class WishlistListView(generics.ListAPIView):
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related('product')


class AddWishlistItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=AddWishlistItemSerializer,
        responses={201: WishlistItemSerializer, 400: None},
        examples=[OpenApiExample('Request example', value={'product_id': 1}, request_only=True)],
    )
    def post(self, request):
        serializer = AddWishlistItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data['product_id']

        product = get_object_or_404(Product, id=product_id)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)

        if not created:
            return Response({'detail': 'این محصول از قبل در لیست علاقه‌مندی‌هاست'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(WishlistItemSerializer(item).data, status=status.HTTP_201_CREATED)


class RemoveWishlistItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={204: None})
    def delete(self, request, item_id):
        item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)