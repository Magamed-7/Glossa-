from django.contrib import admin
from django.utils.html import format_html

from .models import AIRequestLog


@admin.register(AIRequestLog)
class AIRequestLogAdmin(admin.ModelAdmin):
    list_display = (
        "request_icon",
        "short_user",
        "request_type_badge",
        "status_badge",
        "tokens_badge",
        "response_time_badge",
        "created_at",
    )

    list_display_links = (
        "request_icon",
    )

    list_filter = (
        "request_type",
        "status",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__username",
        "prompt",
        "response",
        "error_message",
    )

    readonly_fields = (
        "id",
        "user",
        "request_type",
        "prompt",
        "response",
        "status",
        "error_message",
        "tokens_used",
        "response_time_ms",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 25
    date_hierarchy = "created_at"

    list_select_related = (
        "user",
    )

    fieldsets = (
        (
            "🤖 Информация о запросе",
            {
                "fields": (
                    "id",
                    "user",
                    "request_type",
                    "status",
                )
            },
        ),
        (
            "📝 Prompt",
            {
                "fields": (
                    "prompt",
                )
            },
        ),
        (
            "💬 Ответ AI",
            {
                "fields": (
                    "response",
                )
            },
        ),
        (
            "❌ Ошибки",
            {
                "classes": ("collapse",),
                "fields": (
                    "error_message",
                )
            },
        ),
        (
            "📊 Метрики",
            {
                "fields": (
                    "tokens_used",
                    "response_time_ms",
                    "created_at",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="🤖 Запрос")
    def request_icon(self, obj):
        icons = {
            "generate_story": "📖 История",
            "explain_word": "📚 Слово",
            "explain_grammar": "📝 Грамматика",
            "generate_question": "❓ Вопрос",
            "translate": "🌍 Перевод",
        }

        return icons.get(obj.request_type, "🤖 AI")

    @admin.display(description="👤 Пользователь")
    def short_user(self, obj):
        if obj.user:
            return obj.user.username
        return "👻 Удалён"

    @admin.display(description="🧠 Тип запроса")
    def request_type_badge(self, obj):
        colors = {
            "generate_story": "#8e44ad",
            "explain_word": "#3498db",
            "explain_grammar": "#e67e22",
            "generate_question": "#16a085",
            "translate": "#2980b9",
        }

        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.request_type, "#34495e"),
            obj.get_request_type_display()
        )

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        colors = {
            "success": "#27ae60",
            "failed": "#e74c3c",
            "cached": "#f39c12",
        }

        icons = {
            "success": "🟢",
            "failed": "🔴",
            "cached": "🟡",
        }

        return format_html(
            '<b style="color:{};">{} {}</b>',
            colors.get(obj.status, "#34495e"),
            icons.get(obj.status, "⚪"),
            obj.get_status_display(),
        )

    @admin.display(description="🪙 Токены")
    def tokens_badge(self, obj):
        return format_html(
            '<span style="font-weight:600;">{} ток.</span>',
            f"{obj.tokens_used:,}"
        )

    @admin.display(description="⚡ Ответ")
    def response_time_badge(self, obj):
        if obj.response_time_ms < 1000:
            color = "#27ae60"
        elif obj.response_time_ms < 3000:
            color = "#f39c12"
        else:
            color = "#e74c3c"

        return format_html(
            '<span style="color:{}; font-weight:600;">{} ms</span>',
            color,
            obj.response_time_ms,
        )