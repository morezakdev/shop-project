from django.contrib import admin
from module_common.admin import JalaliAdminMixin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('total_price',)


@admin.register(Cart)
class CartAdmin(JalaliAdminMixin, admin.ModelAdmin):
    jalali_date_fields = ['updated_at']
    list_display = ('user', 'total_items', 'total_price', 'jalali_updated_at')
    inlines = [CartItemInline]
    search_fields = ('user__phone_number',)