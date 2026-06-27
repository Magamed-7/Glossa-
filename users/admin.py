from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, EmailVerification, Friendship, UserLanguage


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    model = User

    list_display = (
        "email",
        "username",
        "phone",
        "verified_badge",
        "staff_badge",
        "active_badge",
        "dashboard_role",
        "created_at",
        "last_login",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_verified",
        "dashboard_role",
        "push_enabled",
    )

    search_fields = (
        "email",
        "username",
        "phone",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("👤 Основное", {
            "fields": (
                "email",
                "username",
                "phone",
                "password",
            )
        }),
        ("⚙️ Права", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "is_verified",
                "dashboard_role",
                "groups",
                "user_permissions",
            )
        }),
        ("🔔 Push-уведомления", {
            "fields": (
                "push_enabled",
                "push_token",
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
        "telegram_badge",
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
        ("🤖 Telegram", {
            "fields": (
                "telegram_chat_id",
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

    @admin.display(description="🤖 Telegram")
    def telegram_badge(self, obj):
        return "🟢 Привязан" if obj.telegram_chat_id else "—"


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "code",
        "is_used",
        "is_expired_badge",
        "created_at",
        "expires_at",
    )

    list_filter = (
        "is_used",
    )

    search_fields = (
        "user__email",
        "user__username",
        "code",
    )

    autocomplete_fields = ("user",)

    ordering = ("-created_at",)

    fieldsets = (
        ("📧 Верификация", {
            "fields": (
                "user",
                "code",
                "is_used",
            )
        }),
        ("⏰ Время", {
            "fields": (
                "created_at",
                "expires_at",
            )
        }),
    )

    readonly_fields = ("created_at", "expires_at")

    @admin.display(description="⏰ Истёк")
    def is_expired_badge(self, obj):
        return "🔴 Да" if obj.is_expired else "🟢 Нет"


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):

    list_display = (
        "from_user",
        "to_user",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "from_user__username",
        "from_user__email",
        "to_user__username",
        "to_user__email",
    )

    autocomplete_fields = ("from_user", "to_user")

    ordering = ("-created_at",)

    fieldsets = (
        ("🤝 Дружба", {
            "fields": (
                "from_user",
                "to_user",
                "status",
            )
        }),
        ("📡 Время", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(UserLanguage)
class UserLanguageAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "language_code",
        "level",
        "show_level",
        "created_at",
    )

    list_filter = (
        "level",
        "show_level",
        "language_code",
    )

    search_fields = (
        "user__username",
        "user__email",
        "language_code",
    )

    autocomplete_fields = ("user",)

    ordering = ("-created_at",)

    fieldsets = (
        ("🌍 Изучаемый язык", {
            "fields": (
                "user",
                "language_code",
                "level",
                "show_level",
            )
        }),
        ("📡 Система", {
            "fields": (
                "created_at",
            )
        }),
    )

    readonly_fields = ("created_at",)
