from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Plan, Subscription, PaymentEvent, TrialPeriod, PaymentRequest


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


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):

    list_display = (
        "user_email",
        "plan_name",
        "amount_badge",
        "status_badge",
        "created_at",
        "confirm_button",
    )

    list_filter = (
        "status",
        "plan",
    )

    search_fields = (
        "user__email",
        "user__username",
    )

    autocomplete_fields = (
        "user",
        "plan",
        "confirmed_by",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "confirmed_at")

    fieldsets = (
        ("👤 Запрос", {
            "fields": (
                "user",
                "plan",
                "amount",
                "currency",
                "status",
            )
        }),
        ("✅ Подтверждение", {
            "fields": (
                "confirmed_by",
                "confirmed_at",
                "admin_note",
            )
        }),
        ("📡 Система", {
            "fields": (
                "created_at",
            )
        }),
    )

    actions = ["confirm_payments", "reject_payments"]

    @admin.display(description="👤 Пользователь")
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description="💳 Тариф")
    def plan_name(self, obj):
        return obj.plan.name

    @admin.display(description="💰 Сумма")
    def amount_badge(self, obj):
        return format_html('<b>{} {}</b>', obj.amount, obj.currency)

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        colors = {
            "pending": "#f39c12",
            "confirmed": "#27ae60",
            "rejected": "#e74c3c",
        }
        icons = {
            "pending": "⏳",
            "confirmed": "✅",
            "rejected": "❌",
        }
        return format_html(
            '<b style="color:{};">{} {}</b>',
            colors.get(obj.status, "#000"),
            icons.get(obj.status, ""),
            obj.get_status_display()
        )

    @admin.display(description="⚡ Действие")
    def confirm_button(self, obj):
        if obj.status != 'pending':
            return "—"
        return format_html(
            '<a href="/admin/subscriptions/paymentrequest/{}/change/" '
            'style="color:#27ae60;font-weight:700;">Подтвердить</a>',
            obj.id
        )

    @admin.action(description="✅ Подтвердить выбранные")
    def confirm_payments(self, request, queryset):
        from datetime import timedelta
        count = 0
        for pr in queryset.filter(status='pending'):
            period_map = {
                'monthly': timedelta(days=30),
                'annual': timedelta(days=365),
            }
            duration = period_map.get(pr.plan.period, timedelta(days=30))
            now = timezone.now()

            subscription = Subscription.objects.create(
                user=pr.user,
                plan=pr.plan,
                status='active',
                started_at=now,
                expires_at=now + duration,
            )

            PaymentEvent.objects.create(
                subscription=subscription,
                method='card',
                amount=pr.amount,
                currency=pr.currency,
                status='success',
                is_demo=False,
            )

            pr.status = 'confirmed'
            pr.confirmed_by = request.user
            pr.confirmed_at = now
            pr.save()
            count += 1

        self.message_user(request, f"Подтверждено: {count} запрос(ов)")

    @admin.action(description="❌ Отклонить выбранные")
    def reject_payments(self, request, queryset):
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"Отклонено: {count} запрос(ов)")
