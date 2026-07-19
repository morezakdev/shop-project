from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("نام", max_length=100)
    slug = models.SlugField("اسلاگ", max_length=120, unique=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="children",
        null=True, blank=True, verbose_name="دسته والد"
    )
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Product(models.Model):
    categories = models.ManyToManyField(
        Category, related_name="products", verbose_name="دسته‌بندی‌ها"
    )
    name = models.CharField("نام", max_length=200)
    slug = models.SlugField("اسلاگ", max_length=220, unique=True, blank=True)
    description = models.TextField("توضیحات", blank=True)
    image = models.ImageField("تصویر", upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants",
        verbose_name="محصول"
    )
    color = models.CharField("رنگ", max_length=50, blank=True)
    size = models.CharField("سایز", max_length=50, blank=True)
    price = models.DecimalField("قیمت", max_digits=12, decimal_places=0)
    stock = models.PositiveIntegerField("موجودی", default=0)
    sku = models.CharField("کد انبار (SKU)", max_length=50, unique=True)

    class Meta:
        verbose_name = "تنوع محصول"
        verbose_name_plural = "تنوع‌های محصول"

    def __str__(self):
        parts = [self.product.name]
        if self.color:
            parts.append(self.color)
        if self.size:
            parts.append(self.size)
        return " - ".join(parts)

    @property
    def is_available(self):
        return self.stock > 0