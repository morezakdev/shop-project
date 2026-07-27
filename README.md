# Shop API — DRF E-Commerce Backend

یک بک‌اند فروشگاهی کامل با **Django REST Framework**، شامل احراز هویت مبتنی بر OTP، مدیریت محصولات، سبد خرید هوشمند با مکانیزم رزرو موجودی، سیستم سفارش، کد تخفیف، و اتصال به درگاه پرداخت زرین‌پال.

این پروژه به‌عنوان یک **قالب پایه (Template)** برای پروژه‌های فروشگاهی بعدی طراحی شده و روی معماری امن، مقاوم در برابر race condition، و قابل تست تمرکز داره.

---

## ویژگی‌ها

### احراز هویت (`module_accounts`)
- ثبت‌نام و لاگین با شماره موبایل + رمز عبور
- تایید هویت با کد یک‌بارمصرف (OTP) با انقضای ۲ دقیقه‌ای
- فراموشی و بازیابی رمز عبور با OTP
- احراز هویت با JWT (Access / Refresh Token)
- Logout با Blacklist کردن Refresh Token
- Throttling روی درخواست‌های OTP
- Dashboard خلاصه (پروفایل + سفارش‌های اخیر + Wishlist اخیر)

### محصولات و دسته‌بندی (`module_catalog`)
- دسته‌بندی سلسله‌مراتبی (والد/فرزند)
- رابطه چندبه‌چند بین محصول و دسته‌بندی
- تنوع محصول (رنگ/سایز) با قیمت و موجودی مستقل
- جستجو، مرتب‌سازی، فیلتر بر اساس دسته‌بندی
- Pagination
- اعتبارسنجی حجم و فرمت تصویر

### سبد خرید (`module_cart`)
- معماری **دو شمارنده‌ی جدا**: موجودی واقعی انبار دست‌نخورده می‌ماند تا لحظه‌ی خرید قطعی؛ رزرو سبد به‌صورت پویا محاسبه می‌شود
- سقف رزرو ۷۰٪ از موجودی برای جلوگیری از سوءاستفاده (Cart Hoarding)
- انقضای خودکار آیتم‌های سبد بعد از ۳ ساعت (Lazy Expiration)
- کول‌داون بعد از انقضای رزرو
- Throttling روی افزودن به سبد

### سفارش و پرداخت (`module_orders`, `module_payments`)
- تبدیل سبد به سفارش با Snapshot قیمت لحظه‌ی خرید (مصون از تغییرات بعدی قیمت)
- مسیر خرید سریع (Quick Buy) بدون نیاز به سبد
- کد تخفیف درصدی با محدودیت تعداد استفاده کل
- اتصال به درگاه پرداخت **زرین‌پال (Sandbox)**
- Idempotency در پردازش وبهوک پرداخت
- جلوگیری از Race Condition با `select_for_update`
- ارسال پیامک تایید سفارش بعد از پرداخت موفق (شبیه‌سازی‌شده)

### لیست علاقه‌مندی‌ها (`module_wishlist`)
- افزودن/حذف محصول به لیست علاقه‌مندی‌ها

### زیرساخت مشترک (`module_common`)
- نمایش خودکار تاریخ‌ها به فرمت جلالی در API و پنل ادمین (بدون تغییر ذخیره‌سازی میلادی در دیتابیس)
- Exception Handler سفارشی برای پیام‌های خطای فارسی

---

## تکنولوژی‌ها

| بخش | تکنولوژی |
|---|---|
| فریم‌ورک | Django + Django REST Framework |
| احراز هویت | djangorestframework-simplejwt |
| مستندسازی API | drf-spectacular (Swagger / OpenAPI) |
| دیتابیس (توسعه) | SQLite |
| درگاه پرداخت | زرین‌پال (Sandbox) |
| تاریخ جلالی | jdatetime |
| تست | Django TestCase + DRF APIClient |

---

## نصب و راه‌اندازی (محیط توسعه)

### ۱. کلون و محیط مجازی

```bash
git clone <repo-url>
cd shop-project
python -m venv venv
venv\Scripts\Activate.ps1      # ویندوز (PowerShell)
# source venv/bin/activate     # لینوکس/مک
```

### ۲. نصب پکیج‌ها

```bash
pip install -r requirements.txt
```

### ۳. تنظیم متغیرهای محیطی

فایل `.env` را کنار `manage.py` بسازید (نمونه در `.env.example`):

```
SECRET_KEY=your-secret-key
DEBUG=True

ZARINPAL_MERCHANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ZARINPAL_SANDBOX=True
ZARINPAL_CALLBACK_URL=http://127.0.0.1:8000/api/payments/callback/
```

### ۴. مایگریشن و اجرا

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

سرور روی `http://127.0.0.1:8000` بالا می‌آید.

---

## مستندات API (Swagger)

بعد از اجرای سرور:

```
http://127.0.0.1:8000/api/docs/
```

---

## نقشه‌ی Endpoint ها

### احراز هویت — `/api/users/`
| متد | مسیر | توضیح |
|---|---|---|
| POST | `register/` | ثبت‌نام + ارسال OTP |
| POST | `verify-otp/` | تایید OTP و دریافت توکن |
| POST | `login/` | ورود |
| POST | `forgot-password/` | ارسال OTP بازیابی رمز |
| POST | `reset-password/` | تغییر رمز با OTP |
| POST | `logout/` | خروج (Blacklist توکن) |
| POST | `token/refresh/` | تمدید Access Token |
| GET | `profile/` | مشاهده پروفایل (فقط‌خواندنی) |
| GET | `dashboard/` | خلاصه‌ی پنل کاربری |

### محصولات — `/api/catalog/`
| متد | مسیر | توضیح |
|---|---|---|
| GET | `categories/` | لیست دسته‌بندی‌ها |
| GET | `products/` | لیست محصولات (search, ordering, category filter) |
| GET | `products/<slug>/` | جزئیات یک محصول |

### سبد خرید — `/api/cart/`
| متد | مسیر | توضیح |
|---|---|---|
| GET | `` | مشاهده سبد |
| POST | `items/` | افزودن آیتم |
| PATCH | `items/<id>/` | تغییر تعداد |
| DELETE | `items/<id>/remove/` | حذف آیتم |

### سفارش — `/api/orders/`
| متد | مسیر | توضیح |
|---|---|---|
| POST | `checkout/` | ثبت سفارش از سبد + شروع پرداخت |
| POST | `quick-buy/` | خرید سریع بدون سبد |
| GET | `` | لیست سفارش‌های کاربر |
| GET | `<id>/` | جزئیات سفارش |

### پرداخت — `/api/payments/`
| متد | مسیر | توضیح |
|---|---|---|
| GET | `callback/` | Callback زرین‌پال (تایید تراکنش) |

### لیست علاقه‌مندی‌ها — `/api/wishlist/`
| متد | مسیر | توضیح |
|---|---|---|
| GET | `` | لیست علاقه‌مندی‌ها |
| POST | `add/` | افزودن محصول |
| DELETE | `<id>/remove/` | حذف از لیست |

---

## اجرای تست‌ها

```bash
python manage.py test
```

برای اجرای تست‌های یک اپ خاص:

```bash
python manage.py test module_cart
```

---

## ساختار پروژه

```
shop-project/
├── manage.py
├── shop_api/            # تنظیمات اصلی پروژه
├── module_accounts/     # احراز هویت و کاربر
├── module_catalog/      # محصول و دسته‌بندی
├── module_cart/         # سبد خرید
├── module_orders/       # سفارش و کوپن
├── module_payments/     # درگاه پرداخت
├── module_wishlist/     # علاقه‌مندی‌ها
├── module_common/       # ابزارهای مشترک (تاریخ جلالی، خطاها)
├── requirements.txt
└── .env
```

---

## نکات امنیتی و معماری

- موجودی محصول با **دو شمارنده‌ی جدا** (موجودی واقعی / رزرو پویا) مدیریت می‌شود تا نه سوءاستفاده از رزرو ممکن باشد، نه فشار غیرضروری روی دیتابیس.
- عملیات حساس (کاهش موجودی، اعمال کوپن) با `select_for_update` قفل می‌شوند تا در برابر درخواست‌های همزمان امن بمانند.
- قیمت سفارش به‌صورت Snapshot ذخیره می‌شود و از تغییرات بعدی قیمت محصول مصون است.
- Webhook پرداخت Idempotent است — پردازش تکراری یک تراکنش موفق یا ناموفق را دوباره انجام نمی‌دهد.

---

## قبل از استفاده در Production

این پروژه برای **توسعه و یادگیری** پیکربندی شده. قبل از انتشار واقعی حتماً:

- مهاجرت از SQLite به PostgreSQL
- تنظیم `DEBUG=False` و `ALLOWED_HOSTS`
- فعال‌سازی HTTPS و تنظیمات امنیتی کوکی/CSRF
- استفاده از `merchant_id` واقعی زرین‌پال (`ZARINPAL_SANDBOX=False`)
- سرو فایل‌های static/media از طریق Nginx یا سرویس ابری
- اجرای پروژه با Gunicorn/uWSGI پشت Nginx (نه `runserver`)

---

## لایسنس

این پروژه صرفاً برای اهداف یادگیری و استفاده‌ی شخصی ساخته شده است.