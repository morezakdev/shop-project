from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from module_common.serializers import JalaliModelSerializer

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)
    password = serializers.CharField(write_only=True)

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value, is_active=True).exists():
            raise serializers.ValidationError("این شماره قبلاً ثبت‌نام کرده است")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)
    otp_code = serializers.CharField(max_length=6)


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)
    password = serializers.CharField(write_only=True)


class ForgotPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)


class ResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class MessageResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class OTPResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    otp_code = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserProfileSerializer(JalaliModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone_number", "is_active", "date_joined"]
        read_only_fields = fields
