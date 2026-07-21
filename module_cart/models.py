from django.db import models
from django.conf import settings
from module_catalog.models import ProductVariant


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name="کاربر"
    )
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"

    def __str__(self):
        return f"سبد {self.user.phone_number}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items', verbose_name="سبد"
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name='cart_items',
        verbose_name="تنوع محصول"
    )
    quantity = models.PositiveIntegerField("تعداد", default=1)
    created_at = models.DateTimeField("تاریخ افزودن", auto_now_add=True)

    class Meta:
        verbose_name = "آیتم سبد"
        verbose_name_plural = "آیتم‌های سبد"
        unique_together = ('cart', 'variant')

    def __str__(self):
        return f"{self.variant} × {self.quantity}"

    @property
    def total_price(self):
        return self.variant.price * self.quantity