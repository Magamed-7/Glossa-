from django.contrib import admin
from django.utils.html import format_html

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "type_badge",
        "user",
        "title_short",
        "status_badge",
        "related_objects",
        "created_at",
    )

    list_filter = (
        "notification_type",
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
            "subscription_expired": "💳",
            "subscription_expiring": "⏳",
            "new_story": "📖",
            "system": "⚙️",
        }

        return f"{icons.get(obj.notification_type, '🔔')} {obj.get_notification_type_display()}"

    @admin.display(description="🧾 Заголовок")
    def title_short(self, obj):
        return obj.title[:60]

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