from django.contrib import admin
from django.utils.html import format_html

from .models import Language, CEFRLevel


class CEFRLevelInline(admin.TabularInline):
    model = CEFRLevel
    extra = 0
    fields = ("level", "order", "min_vocabulary", "max_vocabulary")
    show_change_link = True


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):

    list_display = (
        "language_badge",
        "code_badge",
        "active_badge",
        "levels_count",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "native_name",
        "code",
    )

    ordering = ("name",)

    inlines = (
        CEFRLevelInline,
    )

    fieldsets = (
        ("🌍 Язык", {
            "fields": (
                "name",
                "native_name",
                "code",
                "flag_emoji",
            )
        }),
        ("📘 Описание", {
            "fields": (
                "description",
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

    @admin.display(description="🌍 Язык")
    def language_badge(self, obj):
        return format_html(
            "<b style='font-size:14px;'>{} {}</b>",
            obj.flag_emoji or "🌐",
            obj.name
        )

    @admin.display(description="🧾 Код")
    def code_badge(self, obj):
        return format_html(
            "<code style='font-size:13px;'>{}</code>",
            obj.code
        )

    @admin.display(description="📡 Активен")
    def active_badge(self, obj):
        if obj.is_active:
            return "🟢 Да"
        return "🔴 Нет"

    @admin.display(description="📊 Уровни")
    def levels_count(self, obj):
        count = obj.cefr_levels.count()
        return f"{count} уровней"
    




@admin.register(CEFRLevel)
class CEFRLevelAdmin(admin.ModelAdmin):

    list_display = (
        "level_badge",
        "language",
        "title",
        "vocab_range",
        "order",
    )

    list_filter = (
        "level",
        "language",
    )

    search_fields = (
        "title",
        "description",
        "language__name",
    )

    autocomplete_fields = (
        "language",
    )

    ordering = ("language", "order")

    fieldsets = (
        ("🎯 Уровень", {
            "fields": (
                "language",
                "level",
                "title",
                "description",
            )
        }),
        ("📚 Словарь", {
            "fields": (
                "min_vocabulary",
                "max_vocabulary",
            )
        }),
        ("⚙️ Порядок", {
            "fields": (
                "order",
            )
        }),
    )

    @admin.display(description="🎯 CEFR")
    def level_badge(self, obj):
        colors = {
            "A1": "#2ecc71",
            "A2": "#27ae60",
            "B1": "#3498db",
            "B2": "#2980b9",
            "C1": "#8e44ad",
            "C2": "#2c3e50",
        }

        return format_html(
            "<b style='color:{};font-size:13px;'>{}</b>",
            colors.get(obj.level, "#000"),
            obj.level
        )

    @admin.display(description="📊 Словарь")
    def vocab_range(self, obj):
        return f"{obj.min_vocabulary} — {obj.max_vocabulary}"