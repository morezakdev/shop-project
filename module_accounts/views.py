from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer, VerifyOTPSerializer,
    LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        password = serializer.validated_data['password']

        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={'is_active': False}
        )
        user.set_password(password)
        otp = user.generate_otp()

        return Response({
            'detail': 'کد تایید ارسال شد',
            'otp_code': otp,  # فقط برای تست - بعداً حذف میشه
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({'detail': 'کاربر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_otp_valid(otp_code):
            return Response({'detail': 'کد تایید نامعتبر یا منقضی شده'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.otp_code = None
        user.otp_expire = None
        user.save()

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({'detail': 'شماره یا رمز اشتباه است'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({'detail': 'شماره یا رمز اشتباه است'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({'detail': 'حساب کاربری فعال نیست'}, status=status.HTTP_400_BAD_REQUEST)

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({'detail': 'کاربری با این شماره یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        otp = user.generate_otp()
        return Response({
            'detail': 'کد تایید ارسال شد',
            'otp_code': otp,  # فقط برای تست
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({'detail': 'کاربر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_otp_valid(otp_code):
            return Response({'detail': 'کد تایید نامعتبر یا منقضی شده'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.otp_code = None
        user.otp_expire = None
        user.save()

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)