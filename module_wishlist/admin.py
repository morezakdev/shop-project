from django.contrib import admin
from module_common.admin import JalaliAdminMixin
from .models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(JalaliAdminMixin, admin.ModelAdmin):
    jalali_date_fields = ['created_at']
    list_display = ('user', 'product', 'jalali_created_at')
    search_fields = ('user__phone_number', 'product__name')