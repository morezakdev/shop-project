from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    list_display = ('phone_number', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff')
    ordering = ('-date_joined',)
    search_fields = ('phone_number',)

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('OTP', {'fields': ('otp_code', 'otp_expire')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2'),
        }),
    )


admin.site.register(User, UserAdmin)