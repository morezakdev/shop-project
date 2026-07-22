from django.urls import path
from .views import OrderListView, OrderDetailView, CheckoutView, QuickBuyView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('quick-buy/', QuickBuyView.as_view(), name='quick-buy'),
    path('', OrderListView.as_view(), name='order-list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
]