from django.urls import path
from .views import WishlistListView, AddWishlistItemView, RemoveWishlistItemView

urlpatterns = [
    path('', WishlistListView.as_view(), name='wishlist-list'),
    path('add/', AddWishlistItemView.as_view(), name='wishlist-add'),
    path('<int:item_id>/remove/', RemoveWishlistItemView.as_view(), name='wishlist-remove'),
]