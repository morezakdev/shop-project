from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.throttling import ScopedRateThrottle
from .serializers import (
    RegisterSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    MessageResponseSerializer,
    OTPResponseSerializer,
    TokenResponseSerializer,
)
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import LogoutSerializer

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    @extend_schema(
        request=RegisterSerializer,
        responses={200: OTPResponseSerializer},
        examples=[
            OpenApiExample(
                "Request example",
                value={"phone_number": "09121234567", "password": "123456"},
                request_only=True,
            ),
            OpenApiExample(
                "Successful response",
                value={"detail": "OTP code sent", "otp_code": "482913"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        password = serializer.validated_data["password"]

        user, created = User.objects.get_or_create(
            phone_number=phone_number, defaults={"is_active": False}
        )
        user.set_password(password)
        otp = user.generate_otp()

        return Response(
            {
                "detail": "کد تایید ارسال شد",
                "otp_code": otp,  # فقط برای تست - بعداً حذف میشه
            },
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=VerifyOTPSerializer,
        responses={
            200: TokenResponseSerializer,
            400: MessageResponseSerializer,
            404: MessageResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Request example",
                value={"phone_number": "09121234567", "otp_code": "482913"},
                request_only=True,
            ),
            OpenApiExample(
                "Verified successfully",
                value={
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "User not found",
                value={"detail": "کاربر یافت نشد"},
                response_only=True,
                status_codes=["404"],
            ),
            OpenApiExample(
                "Invalid or expired code",
                value={"detail": "کد تایید نامعتبر یا منقضی شده"},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        otp_code = serializer.validated_data["otp_code"]

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {"detail": "کاربر یافت نشد"}, status=status.HTTP_404_NOT_FOUND
            )

        if not user.is_otp_valid(otp_code):
            return Response(
                {"detail": "کد تایید نامعتبر یا منقضی شده"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = True
        user.otp_code = None
        user.otp_expire = None
        user.save()

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: TokenResponseSerializer,
            400: MessageResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Request example",
                value={"phone_number": "09121234567", "password": "123456"},
                request_only=True,
            ),
            OpenApiExample(
                "Login successful",
                value={
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Wrong credentials",
                value={"detail": "شماره یا رمز اشتباه است"},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Account not active",
                value={"detail": "حساب کاربری فعال نیست"},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {"detail": "شماره یا رمز اشتباه است"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "شماره یا رمز اشتباه است"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active:
            return Response(
                {"detail": "حساب کاربری فعال نیست"}, status=status.HTTP_400_BAD_REQUEST
            )

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=ForgotPasswordSerializer,
        responses={
            200: OTPResponseSerializer,
            404: MessageResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Request example",
                value={"phone_number": "09121234567"},
                request_only=True,
            ),
            OpenApiExample(
                "OTP sent",
                value={"detail": "کد تایید ارسال شد", "otp_code": "482913"},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "User not found",
                value={"detail": "کاربری با این شماره یافت نشد"},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        throttle_classes = [ScopedRateThrottle]
        throttle_scope = "otp"
        phone_number = serializer.validated_data["phone_number"]

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {"detail": "کاربری با این شماره یافت نشد"},
                status=status.HTTP_404_NOT_FOUND,
            )

        otp = user.generate_otp()
        return Response(
            {
                "detail": "کد تایید ارسال شد",
                "otp_code": otp,  # فقط برای تست
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: TokenResponseSerializer,
            400: MessageResponseSerializer,
            404: MessageResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Request example",
                value={
                    "phone_number": "09121234567",
                    "otp_code": "482913",
                    "new_password": "newpass123",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Password reset successful",
                value={
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "User not found",
                value={"detail": "کاربر یافت نشد"},
                response_only=True,
                status_codes=["404"],
            ),
            OpenApiExample(
                "Invalid or expired code",
                value={"detail": "کد تایید نامعتبر یا منقضی شده"},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        otp_code = serializer.validated_data["otp_code"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {"detail": "کاربر یافت نشد"}, status=status.HTTP_404_NOT_FOUND
            )

        if not user.is_otp_valid(otp_code):
            return Response(
                {"detail": "کد تایید نامعتبر یا منقضی شده"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.otp_code = None
        user.otp_expire = None
        user.save()

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={200: MessageResponseSerializer, 400: MessageResponseSerializer},
        examples=[
            OpenApiExample(
                "Request example",
                value={"refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                request_only=True,
            ),
            OpenApiExample(
                "Logged out",
                value={"detail": "با موفقیت خارج شدید"},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Invalid token",
                value={"detail": "توکن نامعتبر است"},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "توکن نامعتبر است"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"detail": "با موفقیت خارج شدید"}, status=status.HTTP_200_OK)
