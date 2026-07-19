from django.contrib import admin
from module_common.utils import to_jalali_date
from .models import Category, Product, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "jalali_created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def jalali_created_at(self, obj):
        return to_jalali_date(obj.created_at)

    jalali_created_at.short_description = "تاریخ ایجاد"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "jalali_created_at")
    list_filter = ("is_active", "categories")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("categories",)
    inlines = [ProductVariantInline]

    def jalali_created_at(self, obj):
        return to_jalali_date(obj.created_at)

    jalali_created_at.short_description = "تاریخ ایجاد"
