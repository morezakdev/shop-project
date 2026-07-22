from .utils import to_jalali_date


class JalaliAdminMixin:
    """
    این Mixin رو به هر ModelAdmin اضافه کن، بعد یه لیست از اسم فیلدهای تاریخ
    رو توی jalali_date_fields بده. برای هر کدوم، یه متد نمایشی جلالی خودکار ساخته میشه
    که می‌تونی توی list_display با پیشوند jalali_ استفاده کنی.

    مثال:
        class ProductAdmin(JalaliAdminMixin, admin.ModelAdmin):
            jalali_date_fields = ['created_at']
            list_display = [..., 'jalali_created_at']
    """
    jalali_date_fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.jalali_date_fields:
            method_name = f'jalali_{field_name}'
            if not hasattr(self, method_name):
                setattr(self, method_name, self._make_jalali_method(field_name))

    def _make_jalali_method(self, field_name):
        def method(obj):
            return to_jalali_date(getattr(obj, field_name))
        method.short_description = field_name
        return method