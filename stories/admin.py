from django.contrib import admin
from django.utils.html import format_html

from .models import Story, StoryWord, UserStoryProgress


class StoryWordInline(admin.TabularInline):
    model = StoryWord
    extra = 0
    fields = ("word", "translation", "part_of_speech", "difficulty")
    show_change_link = True


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):

    list_display = (
        "title_badge",
        "language",
        "level",
        "status_badge",
        "source_badge",
        "views_badge",
        "premium_badge",
        "featured_badge",
        "created_at",
    )

    list_filter = (
        "language",
        "cefr_level",
        "status",
        "source",
        "is_premium",
        "is_featured",
    )

    search_fields = (
        "title",
        "content",
        "topic",
        "tags",
    )

    autocomplete_fields = (
        "language",
        "cefr_level",
        "created_by",
    )

    inlines = (StoryWordInline,)

    ordering = ("-created_at",)

    fieldsets = (
        ("📖 История", {
            "fields": (
                "title",
                "content",
                "topic",
                "tags",
            )
        }),
        ("🌍 Классификация", {
            "fields": (
                "language",
                "cefr_level",
                "status",
            )
        }),
        ("⚙️ Метаданные", {
            "fields": (
                "source",
                "is_premium",
                "is_featured",
                "read_time_minutes",
                "views_count",
                "created_by",
            )
        }),
        ("📊 Система", {
            "classes": ("collapse",),
            "fields": (
                "id",
                "created_at",
                "updated_at",
            )
        }),
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    @admin.display(description="📖 История")
    def title_badge(self, obj):
        return format_html("<b>{}</b>", obj.title)

    @admin.display(description="🌍 Язык")
    def language(self, obj):
        return f"{obj.language.flag_emoji} {obj.language.name}"

    @admin.display(description="🎯 Уровень")
    def level(self, obj):
        return obj.cefr_level.level

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        colors = {
            "draft": "#f39c12",
            "pending_review": "#e67e22",
            "published": "#27ae60",
            "rejected": "#e74c3c",
            "archived": "#7f8c8d",
        }
        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.status, "#000"),
            obj.get_status_display()
        )

    @admin.display(description="📥 Источник")
    def source_badge(self, obj):
        icons = {
            "manual": "✍️",
            "ai_generated": "🤖",
            "ai_assisted": "🤖✨",
        }
        return f"{icons.get(obj.source, '')} {obj.get_source_display()}"

    @admin.display(description="👁 Просмотры")
    def views_badge(self, obj):
        return f"{obj.views_count}"

    @admin.display(description="💎 Premium")
    def premium_badge(self, obj):
        return "💎 Да" if obj.is_premium else "—"

    @admin.display(description="⭐ Избранное")
    def featured_badge(self, obj):
        return "⭐ Да" if obj.is_featured else "—"


@admin.register(StoryWord)
class StoryWordAdmin(admin.ModelAdmin):

    list_display = (
        "word",
        "translation",
        "story",
        "pos_badge",
        "difficulty",
    )

    list_filter = (
        "part_of_speech",
        "difficulty",
    )

    search_fields = (
        "word",
        "translation",
    )

    autocomplete_fields = ("story",)

    ordering = ("story",)

    @admin.display(description="🧩 Часть речи")
    def pos_badge(self, obj):
        icons = {
            "noun": "📦",
            "verb": "⚡",
            "adjective": "🎨",
            "adverb": "🏃",
            "pronoun": "👤",
            "preposition": "🔗",
            "conjunction": "➕",
            "other": "•",
        }
        return f"{icons.get(obj.part_of_speech, '')} {obj.get_part_of_speech_display()}"


@admin.register(UserStoryProgress)
class UserStoryProgressAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "story",
        "status_badge",
        "read_count",
        "last_read_at",
    )

    list_filter = (
        "is_completed",
        "story__language",
    )

    search_fields = (
        "user__email",
        "story__title",
    )

    autocomplete_fields = (
        "user",
        "story",
    )

    ordering = ("-last_read_at",)

    @admin.display(description="📊 Статус")
    def status_badge(self, obj):
        return "✅ Завершено" if obj.is_completed else "📖 Читает"
