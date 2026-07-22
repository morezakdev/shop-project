from django.contrib import admin
from module_common.admin import JalaliAdminMixin
from .models import Category, Product, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Category)
class CategoryAdmin(JalaliAdminMixin, admin.ModelAdmin):
    jalali_date_fields = ['created_at']
    list_display = ('name', 'parent', 'is_active', 'jalali_created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(JalaliAdminMixin, admin.ModelAdmin):
    jalali_date_fields = ['created_at']
    list_display = ('name', 'is_active', 'jalali_created_at')
    list_filter = ('is_active', 'categories')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('categories',)
    inlines = [ProductVariantInline]