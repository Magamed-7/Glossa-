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
        "mastered_badge",
        "created_at",
    )

    list_filter = (
        "language",
        "source",
        "is_mastered",
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
        ("📘 Фраза", {
            "fields": (
                "user",
                "language",
                "word",
                "translation",
                "context_sentence",
                "note",
            )
        }),
        ("🔗 Источник", {
            "fields": (
                "source",
                "story_word",
                "grammar_lesson",
            )
        }),
        ("🧠 Статус памяти", {
            "fields": (
                "is_mastered",
                "created_at",
            )
        }),
    )

    readonly_fields = ("created_at",)

    @admin.display(description="🧩 Фраза")
    def phrase_badge(self, obj):
        return format_html(
            "<b>{}</b> → {}",
            obj.word,
            obj.translation
        )

    @admin.display(description="📥 Источник")
    def source_badge(self, obj):
        icons = {
            "story": "📖",
            "manual": "✍️",
            "grammar": "🧠",
            "duel": "⚔️",
        }
        return f"{icons.get(obj.source, '')} {obj.get_source_display()}"

    @admin.display(description="🧠 Выучено")
    def mastered_badge(self, obj):
        return "✅ Да" if obj.is_mastered else "—"
    



@admin.register(ReviewSession)
class ReviewSessionAdmin(admin.ModelAdmin):

    list_display = (
        "phrase",
        "next_review_badge",
        "status_badge",
        "interval_badge",
        "repetitions",
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
            )
        }),
        ("⏰ Время", {
            "fields": (
                "next_review_at",
                "last_reviewed_at",
            )
        }),
    )

    @admin.display(description="📅 Следующее повторение")
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
        return f"{obj.interval_days} дней"