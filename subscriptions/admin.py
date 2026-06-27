from django.contrib import admin
from django.utils.html import format_html
from .models import Plan, Subscription, PaymentEvent, TrialPeriod


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):

    list_display = (
        "name_badge",
        "period",
        "price_badge",
        "active_badge",
        "limits_badge",
    )

    list_filter = (
        "period",
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
                "period",
                "price",
                "currency",
                "description",
            )
        }),
        ("📊 Лимиты", {
            "fields": (
                "stories_per_day",
                "stories_per_week",
                "phrases_per_day",
                "rated_duels_access",
                "global_leaderboard",
                "ai_access",
                "full_catalog_access",
                "ai_story_assist",
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

    @admin.display(description="💰 Цена")
    def price_badge(self, obj):
        return f"{obj.price} {obj.currency}"

    @admin.display(description="📡 Активен")
    def active_badge(self, obj):
        return "🟢 Да" if obj.is_active else "🔴 Нет"

    @admin.display(description="📊 Лимиты")
    def limits_badge(self, obj):
        return f"{obj.stories_per_day}/day · {obj.phrases_per_day} phrases"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "plan",
        "status_badge",
        "trial_badge",
        "active_badge",
        "expires_at",
        "auto_renew",
    )

    list_filter = (
        "status",
        "plan",
        "is_trial",
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
                "is_trial",
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

    @admin.display(description="🧪 Триал")
    def trial_badge(self, obj):
        return "🟢 Да" if obj.is_trial else "—"

    @admin.display(description="✅ Активна")
    def active_badge(self, obj):
        return "🟢 Да" if obj.is_active else "🔴 Нет"


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):

    list_display = (
        "user_email",
        "amount_badge",
        "method_badge",
        "status_badge",
        "demo_badge",
        "created_at",
    )

    list_filter = (
        "status",
        "method",
        "is_demo",
    )

    search_fields = (
        "subscription__user__email",
        "provider_payment_id",
    )

    autocomplete_fields = ("subscription",)

    ordering = ("-created_at",)

    readonly_fields = ("created_at",)

    fieldsets = (
        ("💰 Платёж", {
            "fields": (
                "subscription",
                "method",
                "amount",
                "currency",
                "status",
                "is_demo",
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
    def user_email(self, obj):
        return obj.subscription.user.email

    @admin.display(description="💰 Сумма")
    def amount_badge(self, obj):
        color = "#27ae60" if obj.status == "success" else "#e74c3c" if obj.status == "failed" else "#f39c12"
        return format_html(
            '<b style="color:{};">{} {}</b>',
            color, obj.amount, obj.currency
        )

    @admin.display(description="💳 Метод")
    def method_badge(self, obj):
        return obj.get_method_display()

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        icons = {
            "success": "🟢",
            "failed": "🔴",
            "refunded": "↩️",
            "pending": "⏳",
            "manual": "🤝",
        }
        return f"{icons.get(obj.status, '')} {obj.get_status_display()}"

    @admin.display(description="🧪 Демо")
    def demo_badge(self, obj):
        return "🟢 Да" if obj.is_demo else "—"


@admin.register(TrialPeriod)
class TrialPeriodAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "active_badge",
        "started_at",
        "expires_at",
        "used_badge",
    )

    list_filter = (
        "is_used",
    )

    search_fields = (
        "user__email",
        "user__username",
    )

    autocomplete_fields = (
        "user",
        "subscription",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("🧪 Пробный период", {
            "fields": (
                "user",
                "subscription",
                "started_at",
                "expires_at",
                "is_used",
            )
        }),
    )

    readonly_fields = (
        "created_at",
        "started_at",
        "expires_at",
    )

    @admin.display(description="✅ Активен")
    def active_badge(self, obj):
        return "🟢 Да" if obj.is_active else "🔴 Нет"

    @admin.display(description="📌 Использован")
    def used_badge(self, obj):
        return "🟢 Да" if obj.is_used else "—"
