from django.db import models
from module_orders.models import Order


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'در انتظار پرداخت'),
        (STATUS_SUCCESS, 'موفق'),
        (STATUS_FAILED, 'ناموفق'),
    ]

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='payment', verbose_name="سفارش"
    )
    authority = models.CharField("Authority", max_length=64, blank=True)
    ref_id = models.CharField("شماره پیگیری", max_length=64, blank=True)
    amount = models.DecimalField("مبلغ", max_digits=14, decimal_places=0)
    status = models.CharField(
        "وضعیت", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"

    def __str__(self):
        return f"پرداخت سفارش #{self.order_id} - {self.status}"