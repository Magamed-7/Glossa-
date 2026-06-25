from django.contrib import admin
from django.utils.html import format_html

from .models import Duel, DuelRound, DuelResult


class DuelRoundInline(admin.TabularInline):
    model = DuelRound
    extra = 0
    readonly_fields = (
        "round_number",
        "question_text",
        "correct_answer",
        "answer_player_one",
        "answer_player_two",
        "round_winner",
        "is_draw",
    )

    fields = (
        "round_number",
        "question_text",
        "correct_answer",
        "answer_player_one",
        "answer_player_two",
        "round_winner",
        "is_draw",
    )

    show_change_link = True


class DuelResultInline(admin.StackedInline):
    model = DuelResult
    extra = 0
    can_delete = False


@admin.register(Duel)
class DuelAdmin(admin.ModelAdmin):

    list_display = (
        "battle",
        "language_badge",
        "mode_badge",
        "status_badge",
        "progress_bar",
        "winner_badge",
        "created_at",
    )

    list_display_links = (
        "battle",
    )

    list_filter = (
        "status",
        "mode",
        "language",
        "round_type",
        "created_at",
    )

    search_fields = (
        "player_one__email",
        "player_two__email",
        "winner__email",
    )

    autocomplete_fields = (
        "player_one",
        "player_two",
        "winner",
        "language",
    )

    readonly_fields = (
        "id",
        "created_at",
        "started_at",
        "finished_at",
        "is_active_badge",
    )

    list_select_related = (
        "player_one",
        "player_two",
        "winner",
        "language",
    )

    inlines = (
        DuelRoundInline,
        DuelResultInline,
    )

    ordering = (
        "-created_at",
    )

    fieldsets = (
        (
            "⚔️ Информация о дуэли",
            {
                "fields": (
                    "id",
                    "player_one",
                    "player_two",
                    "language",
                    "mode",
                    "status",
                    "round_type",
                )
            },
        ),
        (
            "🎯 Прогресс",
            {
                "fields": (
                    "total_rounds",
                    "current_round",
                    "winner",
                    "is_active_badge",
                )
            },
        ),
        (
            "⏰ Время",
            {
                "fields": (
                    "started_at",
                    "finished_at",
                    "created_at",
                )
            },
        ),
    )

    @admin.display(description="⚔️ Дуэль")
    def battle(self, obj):
        p2 = obj.player_two.email if obj.player_two else "❓ Ожидание"
        return f"{obj.player_one.email} 🆚 {p2}"

    @admin.display(description="🌍 Язык")
    def language_badge(self, obj):
        return format_html(
            "<b>🌍 {}</b>",
            obj.language
        )

    @admin.display(description="🏅 Режим")
    def mode_badge(self, obj):
        colors = {
            "casual": "#3498db",
            "rated": "#e74c3c",
        }

        icons = {
            "casual": "🎮",
            "rated": "🏆",
        }

        return format_html(
            '<span style="color:{};font-weight:bold;">{} {}</span>',
            colors[obj.mode],
            icons[obj.mode],
            obj.get_mode_display(),
        )

    @admin.display(description="📡 Статус")
    def status_badge(self, obj):
        colors = {
            "waiting": "#f39c12",
            "in_progress": "#3498db",
            "finished": "#27ae60",
            "cancelled": "#e74c3c",
            "draw": "#9b59b6",
        }

        icons = {
            "waiting": "⏳",
            "in_progress": "🔥",
            "finished": "✅",
            "cancelled": "❌",
            "draw": "🤝",
        }

        return format_html(
            '<b style="color:{};">{} {}</b>',
            colors[obj.status],
            icons[obj.status],
            obj.get_status_display(),
        )

    @admin.display(description="📈 Прогресс")
    def progress_bar(self, obj):
        percent = int((obj.current_round / obj.total_rounds) * 100) if obj.total_rounds else 0

        return format_html(
            """
            <div style="width:120px;background:#ddd;border-radius:10px;">
                <div style="
                    width:{}%;
                    background:#27ae60;
                    color:white;
                    text-align:center;
                    border-radius:10px;
                ">
                    {}/{}
                </div>
            </div>
            """,
            percent,
            obj.current_round,
            obj.total_rounds,
        )

    @admin.display(description="👑 Победитель")
    def winner_badge(self, obj):
        if obj.status == "draw":
            return "🤝 Ничья"

        if obj.winner:
            return f"👑 {obj.winner.email}"

        return "—"

    @admin.display(description="🔥 Активна")
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:green;font-weight:bold;">{}</span>',
                '🟢 Да'
            )
        return format_html(
            '<span style="color:red;font-weight:bold;">{}</span>',
            '🔴 Нет'
        )
    




@admin.register(DuelRound)
class DuelRoundAdmin(admin.ModelAdmin):

    list_display = (
        "duel",
        "round_number",
        "winner_display",
        "round_result",
        "started_at",
    )

    list_filter = (
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

    readonly_fields = (
        "started_at",
        "finished_at",
    )

    list_select_related = (
        "duel",
        "round_winner",
        "story_word",
    )

    @admin.display(description="🏆 Победитель")
    def winner_display(self, obj):
        if obj.is_draw:
            return "🤝 Ничья"

        if obj.round_winner:
            return f"👑 {obj.round_winner.email}"

        return "—"

    @admin.display(description="📊 Результат")
    def round_result(self, obj):
        return f"{obj.answer_player_one} ⚔️ {obj.answer_player_two}"
    




@admin.register(DuelResult)
class DuelResultAdmin(admin.ModelAdmin):

    list_display = (
        "duel",
        "score",
        "rating_changes",
        "avg_time",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

    @admin.display(description="🏆 Счёт")
    def score(self, obj):
        return f"{obj.score_player_one} : {obj.score_player_two}"

    @admin.display(description="📈 Рейтинг")
    def rating_changes(self, obj):
        return (
            f"{obj.rating_change_player_one:+} / "
            f"{obj.rating_change_player_two:+}"
        )

    @admin.display(description="⚡ Среднее время")
    def avg_time(self, obj):
        return (
            f"{obj.avg_time_player_one:.2f}s / "
            f"{obj.avg_time_player_two:.2f}s"
        )