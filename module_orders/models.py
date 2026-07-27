from django.db import models
from django.conf import settings
from module_catalog.models import ProductVariant
from django.core.validators import MinValueValidator, MaxValueValidator


class Coupon(models.Model):
    code = models.CharField("کد تخفیف", max_length=50, unique=True)
    percentage = models.PositiveIntegerField(
        "درصد تخفیف", validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    max_uses = models.PositiveIntegerField("حداکثر تعداد استفاده کل")
    used_count = models.PositiveIntegerField("تعداد استفاده‌شده", default=0)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def __str__(self):
        return f"{self.code} ({self.percentage}%)"

    @property
    def is_available(self):
        return self.is_active and self.used_count < self.max_uses


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"

    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار پرداخت"),
        (STATUS_PAID, "پرداخت‌شده"),
        (STATUS_SHIPPED, "ارسال‌شده"),
        (STATUS_DELIVERED, "تحویل داده‌شده"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="کاربر",
    )
    first_name = models.CharField("نام", max_length=255)
    last_name = models.CharField("نام خانوادگی", max_length=255)
    postal_code = models.CharField("کد پستی", max_length=255)
    address = models.TextField("آدرس تحویل")
    status = models.CharField(
        "وضعیت", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    total_price = models.DecimalField("مبلغ کل", max_digits=14, decimal_places=0)
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="کد تخفیف",
    )
    discount_amount = models.DecimalField(
        "مبلغ تخفیف", max_digits=14, decimal_places=0, default=0
    )
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"سفارش #{self.id} - {self.user.phone_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="سفارش"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="تنوع محصول",
    )
    product_name = models.CharField("نام محصول", max_length=200)
    color = models.CharField("رنگ", max_length=50, blank=True)
    size = models.CharField("سایز", max_length=50, blank=True)
    quantity = models.PositiveIntegerField("تعداد")
    price_at_purchase = models.DecimalField(
        "قیمت لحظه خرید", max_digits=12, decimal_places=0
    )

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"

    @property
    def total_price(self):
        return self.price_at_purchase * self.quantity
