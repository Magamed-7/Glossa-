from django.contrib import admin
from django.utils.html import format_html

from .models import Plan, Subscription, PaymentEvent


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):

    list_display = (
        "name_badge",
        "type_badge",
        "price_badge",
        "active_badge",
        "limits_badge",
    )

    list_filter = (
        "plan_type",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = ("price",)

    fieldsets = (
        ("💳 Тариф", {
            "fields": (
                "name",
                "plan_type",
                "price",
                "currency",
                "description",
            )
        }),
        ("📊 Лимиты", {
            "fields": (
                "stories_per_day",
                "phrases_per_day",
                "ai_access",
                "rated_duels_access",
                "full_analytics",
                "full_catalog_access",
            )
        }),
        ("⚙️ Система", {
            "fields": (
                "is_active",
                "created_at",
            )
        }),
    )

    readonly_fields = ("created_at",)

    @admin.display(description="💳 План")
    def name_badge(self, obj):
        return format_html("<b>{}</b>", obj.name)

    @admin.display(description="📦 Тип")
    def type_badge(self, obj):
        return obj.get_plan_type_display()

    @admin.display(description="💰 Цена")
    def price_badge(self, obj):
        return f"{obj.price} {obj.currency}"

    @admin.display(description="📡 Активен")
    def active_badge(self, obj):
        return "🟢 Да" if obj.is_active else "🔴 Нет"

    @admin.display(description="📊 Лимиты")
    def limits_badge(self, obj):
        return f"{obj.stories_per_day}/day stories"
    




@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "plan",
        "status_badge",
        "active_badge",
        "expires_at",
        "auto_renew",
    )

    list_filter = (
        "status",
        "plan",
        "auto_renew",
    )

    search_fields = (
        "user__email",
    )

    autocomplete_fields = (
        "user",
        "plan",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("👤 Подписка", {
            "fields": (
                "user",
                "plan",
                "status",
            )
        }),
        ("⏰ Время", {
            "fields": (
                "started_at",
                "expires_at",
                "cancelled_at",
            )
        }),
        ("⚙️ Настройки", {
            "fields": (
                "auto_renew",
            )
        }),
        ("📡 Система", {
            "fields": (
                "created_at",
            )
        }),
    )

    readonly_fields = ("created_at",)

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        colors = {
            "active": "#27ae60",
            "expired": "#e74c3c",
            "cancelled": "#95a5a6",
            "pending": "#f39c12",
        }

        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.status, "#000"),
            obj.get_status_display()
        )

    @admin.display(description="✅ Активна")
    def active_badge(self, obj):
        return "🟢 Да" if obj.is_active else "🔴 Нет"
    




@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "amount_badge",
        "provider",
        "status_badge",
        "created_at",
    )

    list_filter = (
        "status",
        "provider",
        "currency",
    )

    search_fields = (
        "subscription__user__email",
        "provider_payment_id",
    )

    autocomplete_fields = ("subscription",)

    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        ("💰 Платёж", {
            "fields": (
                "subscription",
                "provider",
                "amount",
                "currency",
                "status",
            )
        }),
        ("🔧 Технические данные", {
            "fields": (
                "provider_payment_id",
                "error_message",
            )
        }),
        ("📡 Система", {
            "fields": (
                "created_at",
            )
        }),
    )

    @admin.display(description="👤 Пользователь")
    def user(self, obj):
        return obj.subscription.user.email

    @admin.display(description="💰 Сумма")
    def amount_badge(self, obj):
        color = "#27ae60" if obj.status == "success" else "#e74c3c" if obj.status == "failed" else "#f39c12"

        return format_html(
            '<b style="color:{};">{} {}</b>',
            color,
            obj.amount,
            obj.currency
        )

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        icons = {
            "success": "🟢",
            "failed": "🔴",
            "refunded": "↩️",
            "pending": "⏳",
        }

        return f"{icons.get(obj.status, '')} {obj.get_status_display()}"