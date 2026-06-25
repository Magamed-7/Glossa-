from django.contrib import admin
from django.utils.html import format_html

from .models import GrammarLesson, GrammarExample, GrammarQuestion, UserGrammarProgress


class GrammarExampleInline(admin.TabularInline):
    model = GrammarExample
    extra = 0
    fields = ("sentence", "translation", "order", "is_from_story")
    readonly_fields = ()
    show_change_link = True


class GrammarQuestionInline(admin.TabularInline):
    model = GrammarQuestion
    extra = 0
    fields = ("question_type", "question_text", "order")
    show_change_link = True


@admin.register(GrammarLesson)
class GrammarLessonAdmin(admin.ModelAdmin):

    list_display = (
        "title_badge",
        "language_badge",
        "level_badge",
        "status_badge",
        "source_badge",
        "premium_badge",
        "order",
        "read_time",
    )

    list_filter = (
        "language",
        "cefr_level",
        "status",
        "source",
        "is_premium",
    )

    search_fields = (
        "title",
        "explanation",
        "tip",
    )

    autocomplete_fields = (
        "language",
        "cefr_level",
        "created_by",
    )

    inlines = (
        GrammarExampleInline,
        GrammarQuestionInline,
    )

    ordering = ("order",)

    fieldsets = (
        ("📘 Основное", {
            "fields": (
                "title",
                "language",
                "cefr_level",
                "status",
            )
        }),
        ("🧠 Контент", {
            "fields": (
                "explanation",
                "tip",
            )
        }),
        ("⚙️ Настройки", {
            "fields": (
                "source",
                "is_premium",
                "order",
                "read_time_minutes",
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

    @admin.display(description="📘 Урок")
    def title_badge(self, obj):
        return format_html("<b>{}</b>", obj.title)

    @admin.display(description="🌍 Язык")
    def language_badge(self, obj):
        return f"🌍 {obj.language}"

    @admin.display(description="🎯 Уровень")
    def level_badge(self, obj):
        return f"🎯 {obj.cefr_level.level}"

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        colors = {
            "draft": "#f39c12",
            "published": "#27ae60",
            "archived": "#7f8c8d",
        }

        return format_html(
            '<b style="color:{};">{}</b>',
            colors[obj.status],
            obj.get_status_display()
        )

    @admin.display(description="🤖 Источник")
    def source_badge(self, obj):
        icons = {
            "manual": "✍️",
            "ai_generated": "🤖",
        }
        return f"{icons.get(obj.source, '')} {obj.get_source_display()}"

    @admin.display(description="💎 Premium")
    def premium_badge(self, obj):
        return "💎 Да" if obj.is_premium else "—"

    @admin.display(description="⏱ Время")
    def read_time(self, obj):
        return f"{obj.read_time_minutes} мин"
    




@admin.register(GrammarExample)
class GrammarExampleAdmin(admin.ModelAdmin):

    list_display = (
        "lesson",
        "sentence_preview",
        "translation_preview",
        "story_flag",
        "order",
    )

    list_filter = (
        "is_from_story",
        "lesson__language",
    )

    search_fields = (
        "sentence",
        "translation",
    )

    autocomplete_fields = (
        "lesson",
        "story",
    )

    ordering = ("lesson", "order")

    @admin.display(description="🧩 Предложение")
    def sentence_preview(self, obj):
        return obj.sentence[:60]

    @admin.display(description="🌍 Перевод")
    def translation_preview(self, obj):
        return obj.translation[:60]

    @admin.display(description="📖 История")
    def story_flag(self, obj):
        return "📖 Да" if obj.is_from_story else "—"
    




@admin.register(GrammarQuestion)
class GrammarQuestionAdmin(admin.ModelAdmin):

    list_display = (
        "lesson",
        "type_badge",
        "question_preview",
        "order",
    )

    list_filter = (
        "question_type",
        "lesson__language",
    )

    search_fields = (
        "question_text",
        "correct_answer",
    )

    autocomplete_fields = ("lesson",)

    ordering = ("lesson", "order")

    @admin.display(description="❓ Тип")
    def type_badge(self, obj):
        icons = {
            "multiple_choice": "🔘",
            "fill_blank": "✍️",
            "true_false": "⚖️",
            "translate": "🌍",
        }

        return f"{icons.get(obj.question_type, '')} {obj.get_question_type_display()}"

    @admin.display(description="🧠 Вопрос")
    def question_preview(self, obj):
        return obj.question_text[:60]
    




@admin.register(UserGrammarProgress)
class UserGrammarProgressAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "lesson",
        "status_badge",
        "score_badge",
        "attempts",
        "progress_badge",
    )

    list_filter = (
        "status",
        "lesson__language",
    )

    search_fields = (
        "user__email",
        "lesson__title",
    )

    autocomplete_fields = ("user", "lesson")

    readonly_fields = (
        "last_attempt_at",
    )

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        colors = {
            "not_started": "#95a5a6",
            "in_progress": "#f39c12",
            "completed": "#27ae60",
        }

        return format_html(
            '<b style="color:{};">{}</b>',
            colors[obj.status],
            obj.get_status_display()
        )

    @admin.display(description="🏆 Баллы")
    def score_badge(self, obj):
        return f"{obj.score}/{obj.max_score}"

    @admin.display(description="📈 Прогресс")
    def progress_badge(self, obj):
        if obj.max_score == 0:
            percent = 0
        else:
            percent = int((obj.score / obj.max_score) * 100)

        color = "#27ae60" if percent >= 70 else "#f39c12"

        return format_html(
            '<b style="color:{};">{}%</b>',
            color,
            percent
        )