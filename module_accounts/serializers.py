from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value, is_active=True).exists():
            raise serializers.ValidationError("این شماره قبلاً ثبت‌ نام کرده است")
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
    new_password = serializers.CharField(write_only=True, min_length=6)