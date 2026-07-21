from django.utils import timezone
from datetime import timedelta
from django.db import transaction

RESERVATION_HOURS = 3


def release_expired_cart_items(cart):
    """
    آیتم‌های سبد که بیشتر از ۳ ساعت از افزودنشون گذشته رو پیدا می‌کنه،
    موجودی رزروشده رو به Variant برمی‌گردونه و خود آیتم رو حذف می‌کنه.
    """
    expire_before = timezone.now() - timedelta(hours=RESERVATION_HOURS)
    expired_items = cart.items.select_related('variant').filter(created_at__lt=expire_before)

    if not expired_items.exists():
        return

    with transaction.atomic():
        for item in expired_items:
            variant = type(item.variant).objects.select_for_update().get(id=item.variant_id)
            variant.stock += item.quantity
            variant.save()
            item.delete()