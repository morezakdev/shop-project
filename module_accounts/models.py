from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils import timezone
import random
from datetime import timedelta
from django.core.validators import RegexValidator

phone_regex = RegexValidator(
    regex=r"^09\d{9}$", message="شماره موبایل باید با 09 شروع شود و ۱۱ رقم باشد"
)


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("شماره موبایل الزامی است")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(
        max_length=11, unique=True, validators=[phone_regex],verbose_name="شماره تلفن"
    )
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expire = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number

    def generate_otp(self):
        self.otp_code = str(random.randint(100000, 999999))
        self.otp_expire = timezone.now() + timedelta(minutes=2)
        self.save()
        return self.otp_code

    def is_otp_valid(self, code):
        if (
            self.otp_code == code
            and self.otp_expire
            and timezone.now() <= self.otp_expire
        ):
            return True
        return False
    
    class Meta:
        verbose_name = "ماژول کاربر"
        verbose_name_plural = "ماژول کاربران"