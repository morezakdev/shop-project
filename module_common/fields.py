import jdatetime
from rest_framework import serializers


class JalaliDateTimeField(serializers.Field):
    """
    فیلد میلادی رو موقع خروجی به جلالی تبدیل می‌کنه.
    فقط برای خواندن (read-only) استفاده میشه - ورودی همچنان میلادی/ISO دریافت میشه.
    """

    def to_representation(self, value):
        if value is None:
            return None
        jalali_dt = jdatetime.datetime.fromgregorian(datetime=value)
        return jalali_dt.strftime('%Y/%m/%d %H:%M:%S')

    def to_internal_value(self, data):
        # این فیلد فقط خروجیه؛ اگه بخوای ورودی جلالی هم قبول کنه باید اینجا پیاده بشه
        raise serializers.ValidationError('این فیلد فقط قابل خواندن است')


class JalaliDateField(serializers.Field):
    """مشابه بالا ولی فقط تاریخ، بدون ساعت"""

    def to_representation(self, value):
        if value is None:
            return None
        jalali_date = jdatetime.date.fromgregorian(date=value)
        return jalali_date.strftime('%Y/%m/%d')

    def to_internal_value(self, data):
        raise serializers.ValidationError('این فیلد فقط قابل خواندن است')