from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

from .models import CartItem, CartReservationCooldown

RESERVATION_HOURS = 3
COOLDOWN_MINUTES = 10
CART_RESERVE_RATIO = 0.7  


def release_expired_cart_items(cart):
    expire_before = timezone.now() - timedelta(hours=RESERVATION_HOURS)
    expired_items = cart.items.select_related("variant").filter(
        created_at__lt=expire_before
    )

    for item in expired_items:
        CartReservationCooldown.objects.update_or_create(
            user=cart.user,
            variant=item.variant,
            defaults={
                "cooldown_until": timezone.now() + timedelta(minutes=COOLDOWN_MINUTES)
            },
        )
        item.delete()


def get_reserved_quantity(variant, exclude_cart_item=None):
    """مجموع تعداد رزروشده این Variant توی همه‌ی سبدهای فعال (همه کاربران)"""
    qs = CartItem.objects.filter(variant=variant)
    if exclude_cart_item:
        qs = qs.exclude(id=exclude_cart_item.id)
    return qs.aggregate(total=Sum("quantity"))["total"] or 0


def get_cart_available(variant, exclude_cart_item=None):
    """چقدر ظرفیت رزرو سبد (سقف ۷۰٪) هنوز باقی مونده"""
    reserved = get_reserved_quantity(variant, exclude_cart_item)
    cap = int(variant.stock * CART_RESERVE_RATIO)
    return max(0, cap - reserved)


def get_quickbuy_available(variant):
    """چقدر برای خرید سریع (کل موجودی منهای رزروشده‌ها) در دسترسه"""
    reserved = get_reserved_quantity(variant)
    return max(0, variant.stock - reserved)


def check_cooldown(user, variant):
    """اگه کول‌داون فعال باشه پیام خطا برمی‌گردونه، وگرنه None"""
    cooldown = CartReservationCooldown.objects.filter(
        user=user, variant=variant
    ).first()
    if cooldown and cooldown.cooldown_until > timezone.now():
        remaining_minutes = (
            int((cooldown.cooldown_until - timezone.now()).total_seconds() // 60) + 1
        )
        return f"به‌دلیل انقضای رزرو قبلی، تا {remaining_minutes} دقیقه دیگر امکان افزودن مجدد این کالا نیست"
    return None
