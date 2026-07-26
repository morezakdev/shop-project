from django.db import models
from django.conf import settings
from module_catalog.models import Product


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='wishlist_items', verbose_name="کاربر"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='wishlisted_by', verbose_name="محصول"
    )
    created_at = models.DateTimeField("تاریخ افزودن", auto_now_add=True)

    class Meta:
        verbose_name = "آیتم علاقه‌مندی"
        verbose_name_plural = "لیست علاقه‌مندی‌ها"
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.phone_number} → {self.product.name}"