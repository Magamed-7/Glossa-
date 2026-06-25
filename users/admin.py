from django.contrib import admin
from django.utils.html import format_html

from .models import User, Profile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    model = User

    list_display = (
        "email",
        "username",
        "verified_badge",
        "staff_badge",
        "active_badge",
        "created_at",
        "last_login",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_verified",
    )

    search_fields = (
        "email",
        "username",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("👤 Основное", {
            "fields": (
                "email",
                "username",
                "password",
            )
        }),
        ("⚙️ Права", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "is_verified",
                "groups",
                "user_permissions",
            )
        }),
        ("📡 Время", {
            "fields": (
                "last_login",
                "created_at",
            )
        }),
    )

    readonly_fields = ("created_at",)

    @admin.display(description="✔️ Верифицирован")
    def verified_badge(self, obj):
        return "🟢 Да" if obj.is_verified else "🔴 Нет"

    @admin.display(description="🛠 Staff")
    def staff_badge(self, obj):
        return "🟢 Да" if obj.is_staff else "—"

    @admin.display(description="📡 Активен")
    def active_badge(self, obj):
        return "🟢 Да" if obj.is_active else "🔴 Нет"
    




@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "full_name",
        "native_language",
        "ui_language",
        "timezone",
        "updated_at",
    )

    list_filter = (
        "ui_language",
        "native_language",
    )

    search_fields = (
        "user__email",
        "full_name",
    )

    autocomplete_fields = ("user",)

    ordering = ("-updated_at",)

    fieldsets = (
        ("👤 Профиль", {
            "fields": (
                "user",
                "full_name",
                "bio",
                "avatar_url",
            )
        }),
        ("🌍 Языки", {
            "fields": (
                "native_language",
                "ui_language",
            )
        }),
        ("⏰ Настройки", {
            "fields": (
                "timezone",
            )
        }),
        ("📡 Система", {
            "fields": (
                "updated_at",
            )
        }),
    )

    readonly_fields = ("updated_at",)