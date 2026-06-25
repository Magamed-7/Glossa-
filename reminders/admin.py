from django.contrib import admin
from django.utils.html import format_html

from .models import Reminder, ReminderSchedule


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):

    list_display = (
        "type_badge",
        "user",
        "title_short",
        "status_badge",
        "scheduled_at",
        "sent_at",
    )

    list_filter = (
        "reminder_type",
        "status",
        "scheduled_at",
    )

    search_fields = (
        "title",
        "body",
        "user__email",
    )

    autocomplete_fields = ("user",)

    ordering = ("-scheduled_at",)

    readonly_fields = (
        "id",
        "created_at",
        "sent_at",
        "error_message",
    )

    fieldsets = (
        ("⏰ Напоминание", {
            "fields": (
                "user",
                "reminder_type",
                "title",
                "body",
            )
        }),
        ("📡 Отправка", {
            "fields": (
                "status",
                "scheduled_at",
                "sent_at",
                "error_message",
            )
        }),
        ("⚙️ Система", {
            "fields": (
                "id",
                "created_at",
            )
        }),
    )

    @admin.display(description="📌 Тип")
    def type_badge(self, obj):
        icons = {
            "daily_review": "📚",
            "streak_warning": "🔥",
            "inactivity": "😴",
            "new_content": "🆕",
            "subscription_expiring": "💳",
        }

        return f"{icons.get(obj.reminder_type, '⏰')} {obj.get_reminder_type_display()}"

    @admin.display(description="🧾 Заголовок")
    def title_short(self, obj):
        return obj.title[:60]

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        colors = {
            "pending": "#f39c12",
            "sent": "#27ae60",
            "failed": "#e74c3c",
            "skipped": "#95a5a6",
        }

        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.status, "#000"),
            obj.get_status_display()
        )
    




@admin.register(ReminderSchedule)
class ReminderScheduleAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "enabled_badge",
        "frequency_badge",
        "preferred_time",
        "timezone",
        "updated_at",
    )

    list_filter = (
        "is_enabled",
        "frequency",
    )

    search_fields = (
        "user__email",
    )

    autocomplete_fields = ("user",)

    ordering = ("-updated_at",)

    fieldsets = (
        ("⚙️ Настройки", {
            "fields": (
                "user",
                "is_enabled",
                "frequency",
            )
        }),
        ("⏰ Время", {
            "fields": (
                "preferred_time",
                "timezone",
            )
        }),
        ("📡 Система", {
            "fields": (
                "updated_at",
            )
        }),
    )

    @admin.display(description="📡 Включено")
    def enabled_badge(self, obj):
        return "🟢 Да" if obj.is_enabled else "🔴 Нет"

    @admin.display(description="⏰ Частота")
    def frequency_badge(self, obj):
        icons = {
            "daily": "📅",
            "every_2_days": "📆",
            "weekly": "🗓️",
            "smart": "🧠",
        }

        return f"{icons.get(obj.frequency, '')} {obj.get_frequency_display()}"