from django.contrib import admin
from django.utils.html import format_html

from .models import UserPhrase, ReviewSession


@admin.register(UserPhrase)
class UserPhraseAdmin(admin.ModelAdmin):

    list_display = (
        "phrase_badge",
        "user",
        "language",
        "source_badge",
        "status_badge",
        "category",
        "created_at",
    )

    list_filter = (
        "language",
        "source",
        "status",
        "category",
    )

    search_fields = (
        "word",
        "translation",
        "user__email",
        "context_sentence",
    )

    autocomplete_fields = (
        "user",
        "language",
        "story_word",
        "grammar_lesson",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("📘 Слово", {
            "fields": (
                "user",
                "language",
                "word",
                "translation",
                "context_sentence",
                "note",
                "category",
            )
        }),
        ("🔗 Источник", {
            "fields": (
                "source",
                "story_word",
                "grammar_lesson",
            )
        }),
        ("🧠 Статус", {
            "fields": (
                "status",
                "created_at",
            )
        }),
    )

    readonly_fields = ("created_at",)

    @admin.display(description="🧩 Слово")
    def phrase_badge(self, obj):
        return format_html("<b>{}</b> → {}", obj.word, obj.translation)

    @admin.display(description="📥 Источник")
    def source_badge(self, obj):
        icons = {
            "story": "📖",
            "manual": "✍️",
            "grammar": "🧠",
            "duel": "⚔️",
        }
        return f"{icons.get(obj.source, '')} {obj.get_source_display()}"

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        colors = {"active": "#f39c12", "mastered": "#27ae60"}
        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.status, "#000"),
            obj.get_status_display()
        )


@admin.register(ReviewSession)
class ReviewSessionAdmin(admin.ModelAdmin):

    list_display = (
        "phrase",
        "next_review_badge",
        "status_badge",
        "interval_badge",
        "repetitions",
        "consecutive_badge",
    )

    list_filter = (
        "last_result",
    )

    search_fields = (
        "phrase__word",
        "phrase__user__email",
    )

    autocomplete_fields = ("phrase",)

    ordering = ("next_review_at",)

    readonly_fields = (
        "easiness_factor",
        "interval_days",
        "repetitions",
        "consecutive_correct",
        "next_review_at",
        "last_reviewed_at",
    )

    fieldsets = (
        ("🧠 Повторение", {
            "fields": (
                "phrase",
                "last_result",
            )
        }),
        ("📊 SM-2 параметры", {
            "fields": (
                "easiness_factor",
                "interval_days",
                "repetitions",
                "consecutive_correct",
            )
        }),
        ("⏰ Время", {
            "fields": (
                "next_review_at",
                "last_reviewed_at",
            )
        }),
    )

    @admin.display(description="📅 Следующее")
    def next_review_badge(self, obj):
        return obj.next_review_at.strftime("%d.%m.%Y")

    @admin.display(description="📡 Результат")
    def status_badge(self, obj):
        colors = {
            "again": "#e74c3c",
            "hard": "#f39c12",
            "good": "#27ae60",
            "easy": "#2ecc71",
        }
        if not obj.last_result:
            return "—"
        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.last_result, "#000"),
            obj.last_result
        )

    @admin.display(description="📈 Интервал")
    def interval_badge(self, obj):
        return f"{obj.interval_days} дн."

    @admin.display(description="✅ Подряд")
    def consecutive_badge(self, obj):
        return f"{obj.consecutive_correct} подряд"