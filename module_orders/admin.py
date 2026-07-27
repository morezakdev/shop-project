from django.contrib import admin
from module_common.utils import to_jalali_date
from .models import Order, OrderItem
from .models import Order, OrderItem, Coupon
from module_common.admin import JalaliAdminMixin


@admin.register(Coupon)
class CouponAdmin(JalaliAdminMixin, admin.ModelAdmin):
    jalali_date_fields = ["created_at"]
    list_display = (
        "code",
        "percentage",
        "used_count",
        "max_uses",
        "is_active",
        "jalali_created_at",
    )
    search_fields = ("code",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "color", "size", "quantity", "price_at_purchase")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "jalali_created_at")
    list_filter = ("status",)
    search_fields = ("user__phone_number", "id")
    inlines = [OrderItemInline]
    readonly_fields = ("user", "total_price", "created_at", "updated_at")

    def jalali_created_at(self, obj):
        return to_jalali_date(obj.created_at)

    jalali_created_at.short_description = "تاریخ ثبت"
