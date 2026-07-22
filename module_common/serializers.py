from rest_framework import serializers
from django.db import models as django_models
from .fields import JalaliDateTimeField, JalaliDateField


class JalaliModelSerializer(serializers.ModelSerializer):
    """
    این کلاس رو به‌جای serializers.ModelSerializer استفاده کن.
    هر فیلد تاریخ (DateTimeField یا DateField) مدل، خودکار به جلالی تبدیل میشه،
    بدون نیاز به override دستی هر فیلد.
    """

    def build_standard_field(self, field_name, model_field):
        field_class, field_kwargs = super().build_standard_field(field_name, model_field)

        if isinstance(model_field, django_models.DateTimeField):
            return JalaliDateTimeField, {'read_only': True}

        if isinstance(model_field, django_models.DateField):
            return JalaliDateField, {'read_only': True}

        return field_class, field_kwargs