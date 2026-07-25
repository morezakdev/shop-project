import requests
from django.conf import settings


def _get_base_url():
    return (
        "https://sandbox.zarinpal.com/pg/v4"
        if settings.ZARINPAL_SANDBOX
        else "https://api.zarinpal.com/pg/v4"
    )


def _get_startpay_url():
    return (
        "https://sandbox.zarinpal.com/pg/StartPay/"
        if settings.ZARINPAL_SANDBOX
        else "https://www.zarinpal.com/pg/StartPay/"
    )


def request_payment(order):
    """
    به زرین‌پال درخواست شروع پرداخت می‌فرسته.
    برمی‌گردونه (authority, payment_url) در صورت موفقیت، یا (None, None) در صورت خطا.
    """
    url = f"{_get_base_url()}/payment/request.json"
    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": int(order.total_price),
        "callback_url": settings.ZARINPAL_CALLBACK_URL,
        "description": f"پرداخت سفارش #{order.id}",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
    except (requests.RequestException, ValueError):
        return None, None

    result = data.get("data") or {}
    if result.get("code") == 100:
        authority = result["authority"]
        payment_url = f"{_get_startpay_url()}{authority}"
        return authority, payment_url

    return None, None


def verify_payment(authority, amount):
    """
    پرداخت رو نزد زرین‌پال تایید می‌کنه.
    برمی‌گردونه (is_success, ref_id).
    """
    url = f"{_get_base_url()}/payment/verify.json"
    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": int(amount),
        "authority": authority,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
    except (requests.RequestException, ValueError):
        return False, None

    result = data.get("data") or {}
    if result.get("code") in (100, 101):  # 101 یعنی قبلاً تایید شده (idempotent)
        return True, result.get("ref_id")

    return False, None
