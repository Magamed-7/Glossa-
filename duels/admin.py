from django.contrib import admin
from django.utils.html import format_html

from .models import Duel, DuelRound, DuelResult


class DuelRoundInline(admin.TabularInline):
    model = DuelRound
    extra = 0
    show_change_link = True

    fields = (
        "round_number",
        "round_type",
        "round_winner",
        "is_draw",
        "started_at",
        "finished_at",
    )

    readonly_fields = (
        "round_number",
        "started_at",
        "finished_at",
    )



class DuelResultInline(admin.StackedInline):
    model = DuelResult
    extra = 0
    can_delete = False


@admin.register(Duel)
class DuelAdmin(admin.ModelAdmin):

    list_display = (
        "battle_display",
        "language_display",
        "level_display",
        "mode_display",
        "opponent_display",
        "status_display",
        "progress_display",
        "winner_display",
        "created_at",
    )

    list_display_links = (
        "battle_display",
    )

    search_fields = (
        "player_one__email",
        "player_two__email",
        "winner__email",
    )

    list_filter = (
        "status",
        "mode",
        "opponent_type",
        "language",
        "cefr_level",
        "created_at",
    )

    autocomplete_fields = (
        "player_one",
        "player_two",
        "winner",
        "language",
        "cefr_level",
    )

    readonly_fields = (
        "id",
        "created_at",
        "started_at",
        "finished_at",
        "is_active_display",
    )

    list_select_related = (
        "player_one",
        "player_two",
        "winner",
        "language",
        "cefr_level",
    )

    ordering = (
        "-created_at",
    )

    date_hierarchy = "created_at"

    inlines = (
        DuelRoundInline,
        DuelResultInline,
    )


    fieldsets = (
        (
            "⚔️ Участники",
            {
                "fields": (
                    "player_one",
                    "player_two",
                    "winner",
                    "is_draw",
                )
            }
        ),
        (
            "🌍 Настройки дуэли",
            {
                "fields": (
                    "language",
                    "cefr_level",
                    "mode",
                    "opponent_type",
                )
            }
        ),
        (
            "🎯 Игровой процесс",
            {
                "fields": (
                    "status",
                    "current_round",
                    "total_rounds",
                    "time_per_round_seconds",
                    "is_active_display",
                )
            }
        ),
        (
            "⏰ Время",
            {
                "fields": (
                    "started_at",
                    "finished_at",
                    "created_at",
                )
            }
        ),
        (
            "🔐 Системная информация",
            {
                "classes": ("collapse",),
                "fields": (
                    "id",
                )
            }
        ),
    )

    @admin.display(description="⚔️ Дуэль")
    def battle_display(self, obj):
        if obj.opponent_type == "ai":
            opponent = "🤖 AI Trainer"
        elif obj.player_two:
            opponent = f"👤 {obj.player_two.email}"
        else:
            opponent = "❓ Ожидание"

        return format_html(
            "<b>👤 {} 🆚 {}</b>",
            obj.player_one.email,
            opponent,
        )

    @admin.display(description="🌍 Язык")
    def language_display(self, obj):
        return f"🌍 {obj.language}"

    @admin.display(description="📚 Уровень")
    def level_display(self, obj):
        return format_html(
            "<b>🎓 {}</b>",
            obj.cefr_level
        )

    @admin.display(description="🏆 Режим")
    def mode_display(self, obj):
        icon = "🎮" if obj.mode == "casual" else "🏅"

        return format_html(
            "<b>{} {}</b>",
            icon,
            obj.get_mode_display(),
        )

    @admin.display(description="🤝 Соперник")
    def opponent_display(self, obj):
        if obj.opponent_type == "ai":
            return "🤖 AI Trainer"

        return "👤 Игрок"

    @admin.display(description="📡 Статус")
    def status_display(self, obj):

        styles = {
            "waiting": ("⏳", "#f39c12"),
            "in_progress": ("🔥", "#3498db"),
            "finished": ("✅", "#27ae60"),
            "cancelled": ("❌", "#e74c3c"),
        }

        icon, color = styles.get(obj.status)

        return format_html(
            '<b style="color:{};">{} {}</b>',
            color,
            icon,
            obj.get_status_display(),
        )

    @admin.display(description="📈 Прогресс")
    def progress_display(self, obj):
        return f"🎯 {obj.current_round}/{obj.total_rounds}"

    @admin.display(description="👑 Победитель")
    def winner_display(self, obj):

        if obj.is_draw:
            return "🤝 Ничья"

        if obj.winner:
            return f"👑 {obj.winner.email}"

        return "—"

    @admin.display(description="🟢 Активна")
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:green;font-weight:bold;">🟢 Активна</span>'
            )

        return format_html(
            '<span style="color:red;font-weight:bold;">🔴 Не активна</span>'
        )




@admin.register(DuelRound)
class DuelRoundAdmin(admin.ModelAdmin):

    list_display = (
        "duel",
        "round_number",
        "round_type_display",
        "winner_display",
        "times_display",
        "started_at",
    )

    list_filter = (
        "round_type",
        "is_draw",
        "duel__language",
    )

    search_fields = (
        "question_text",
        "correct_answer",
    )

    autocomplete_fields = (
        "duel",
        "round_winner",
        "story_word",
    )

    list_select_related = (
        "duel",
        "round_winner",
        "story_word",
    )

    readonly_fields = (
        "started_at",
        "finished_at",
    )

    fieldsets = (
        (
            "❓ Вопрос",
            {
                "fields": (
                    "duel",
                    "round_number",
                    "round_type",
                    "question_text",
                    "correct_answer",
                    "options",
                )
            }
        ),
        (
            "👥 Ответы игроков",
            {
                "fields": (
                    "answer_player_one",
                    "answer_player_two",
                    "time_player_one",
                    "time_player_two",
                )
            }
        ),
        (
            "🏆 Результат",
            {
                "fields": (
                    "round_winner",
                    "is_draw",
                    "story_word",
                )
            }
        ),
        (
            "⏰ Время",
            {
                "fields": (
                    "started_at",
                    "finished_at",
                )
            }
        ),
    )

    @admin.display(description="📝 Тип")
    def round_type_display(self, obj):
        return obj.get_round_type_display()

    @admin.display(description="👑 Победитель")
    def winner_display(self, obj):
        if obj.is_draw:
            return "🤝 Ничья"

        if obj.round_winner:
            return f"👑 {obj.round_winner.email}"

        return "—"

    @admin.display(description="⚡ Скорость")
    def times_display(self, obj):
        return (
            f"👤 {obj.time_player_one or '-'}с | "
            f"🆚 "
            f"{obj.time_player_two or '-'}с"
        )



@admin.register(DuelResult)
class DuelResultAdmin(admin.ModelAdmin):

    list_display = (
        "duel",
        "score_display",
        "rating_display",
        "avg_time_display",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

    autocomplete_fields = (
        "duel",
    )

    @admin.display(description="🏆 Счёт")
    def score_display(self, obj):
        return (
            f"🥇 {obj.score_player_one}"
            f" : "
            f"{obj.score_player_two} 🥈"
        )

    @admin.display(description="📈 Рейтинг")
    def rating_display(self, obj):
        return (
            f"{obj.rating_change_player_one:+} / "
            f"{obj.rating_change_player_two:+}"
        )

    @admin.display(description="⚡ Среднее время")
    def avg_time_display(self, obj):
        return (
            f"{obj.avg_time_player_one or '-'}с "
            f"vs "
            f"{obj.avg_time_player_two or '-'}с"
        )