from django.contrib import admin
from django.utils.html import format_html
from .models import Notification, PushSubscription


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "type_badge",
        "user",
        "title_short",
        "channel_badge",
        "status_badge",
        "related_objects",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "channel",
        "is_read",
        "created_at",
    )

    search_fields = (
        "title",
        "body",
        "user__email",
    )

    autocomplete_fields = (
        "user",
        "duel",
        "story",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "id",
        "created_at",
        "read_at",
    )

    fieldsets = (
        ("🔔 Уведомление", {
            "fields": (
                "user",
                "notification_type",
                "channel",
                "title",
                "body",
            )
        }),
        ("🔗 Связанные объекты", {
            "fields": (
                "duel",
                "story",
            )
        }),
        ("📡 Статус", {
            "fields": (
                "is_read",
                "read_at",
            )
        }),
        ("⚙️ Система", {
            "fields": (
                "id",
                "created_at",
            )
        }),
    )

    @admin.display(description="📡 Тип")
    def type_badge(self, obj):
        icons = {
            "duel_invite": "⚔️",
            "duel_finished": "🏁",
            "duel_cancelled": "❌",
            "rating_changed": "📈",
            "achievement": "🏆",
            "friend_request": "🤝",
            "friend_accepted": "✅",
            "subscription_expired": "💳",
            "subscription_expiring": "⏳",
            "trial_expiring": "🎁",
            "new_story": "📖",
            "review_ready": "📚",
            "system": "⚙️",
        }

        return f"{icons.get(obj.notification_type, '🔔')} {obj.get_notification_type_display()}"

    @admin.display(description="🧾 Заголовок")
    def title_short(self, obj):
        return obj.title[:60]

    @admin.display(description="📨 Канал")
    def channel_badge(self, obj):
        icons = {
            "websocket": "🌐",
            "telegram": "✈️",
            "push": "📲",
        }
        return f"{icons.get(obj.channel, '📡')} {obj.get_channel_display()}"

    @admin.display(description="📬 Статус")
    def status_badge(self, obj):
        if obj.is_read:
            return "✅ Прочитано"
        return "🔴 Новое"

    @admin.display(description="🔗 Связь")
    def related_objects(self, obj):
        parts = []

        if obj.duel:
            parts.append("⚔️ Duel")
        if obj.story:
            parts.append("📖 Story")

        return " | ".join(parts) if parts else "—"


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "endpoint_short",
        "is_active_badge",
        "user_agent_short",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "user__email",
        "endpoint",
        "user_agent",
    )

    autocomplete_fields = ("user",)

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "endpoint",
        "p256dh_key",
        "auth_key",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("📲 Push-подписка", {
            "fields": (
                "user",
                "endpoint",
                "p256dh_key",
                "auth_key",
            )
        }),
        ("📡 Статус", {
            "fields": (
                "is_active",
                "user_agent",
            )
        }),
        ("⚙️ Система", {
            "fields": (
                "id",
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="🔗 Endpoint")
    def endpoint_short(self, obj):
        return f"{obj.endpoint[:50]}..."

    @admin.display(description="📡 Активна")
    def is_active_badge(self, obj):
        return "🟢 Да" if obj.is_active else "🔴 Нет"

    @admin.display(description="🌐 User-Agent")
    def user_agent_short(self, obj):
        return obj.user_agent[:60] if obj.user_agent else "—"