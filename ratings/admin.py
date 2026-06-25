from django.contrib import admin
from django.utils.html import format_html

from .models import PlayerRating, RatingHistory


@admin.register(PlayerRating)
class PlayerRatingAdmin(admin.ModelAdmin):

    list_display = (
        "player_badge",
        "language",
        "score_badge",
        "win_rate_badge",
        "streak_badge",
        "total_duels",
        "updated_at",
    )

    list_filter = (
        "language",
    )

    search_fields = (
        "user__email",
    )

    autocomplete_fields = (
        "user",
        "language",
    )

    ordering = ("-score",)

    readonly_fields = (
        "win_rate_display",
        "updated_at",
    )

    fieldsets = (
        ("🏆 Игрок", {
            "fields": (
                "user",
                "language",
                "score",
            )
        }),
        ("📊 Статистика", {
            "fields": (
                "wins",
                "losses",
                "draws",
                "total_duels",
            )
        }),
        ("🔥 Серии", {
            "fields": (
                "win_streak",
                "best_streak",
            )
        }),
        ("⚙️ Система", {
            "fields": (
                "updated_at",
            )
        }),
    )

    @admin.display(description="👤 Игрок")
    def player_badge(self, obj):
        return obj.user.email

    @admin.display(description="⭐ Рейтинг")
    def score_badge(self, obj):
        color = "#27ae60" if obj.score >= 1200 else "#f39c12" if obj.score >= 1000 else "#e74c3c"

        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            obj.score
        )

    @admin.display(description="📈 Win rate")
    def win_rate_badge(self, obj):
        return f"{obj.win_rate}%"

    @admin.display(description="🔥 Streak")
    def streak_badge(self, obj):
        return f"{obj.win_streak} / {obj.best_streak}"
    
    @admin.display(description="📊 Win rate")
    def win_rate_display(self, obj):
        return f"{obj.win_rate}%"
        




@admin.register(RatingHistory)
class RatingHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "player",
        "change_badge",
        "reason_badge",
        "score_flow",
        "duel",
        "created_at",
    )

    list_filter = (
        "reason",
        "created_at",
    )

    search_fields = (
        "player_rating__user__email",
    )

    autocomplete_fields = (
        "player_rating",
        "duel",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "score_before",
        "score_after",
        "change",
        "created_at",
    )

    fieldsets = (
        ("📊 Изменение", {
            "fields": (
                "player_rating",
                "duel",
                "reason",
            )
        }),
        ("📈 Данные", {
            "fields": (
                "score_before",
                "score_after",
                "change",
            )
        }),
        ("⚙️ Система", {
            "fields": (
                "created_at",
            )
        }),
    )

    @admin.display(description="👤 Игрок")
    def player(self, obj):
        return obj.player_rating.user.email

    @admin.display(description="⚖️ Изменение")
    def change_badge(self, obj):
        color = "#27ae60" if obj.change > 0 else "#e74c3c"

        sign = "+" if obj.change > 0 else ""

        return format_html(
            '<b style="color:{};">{}{}</b>',
            color,
            sign,
            obj.change
        )

    @admin.display(description="📌 Причина")
    def reason_badge(self, obj):
        icons = {
            "duel_win": "🏆",
            "duel_loss": "💀",
            "duel_draw": "🤝",
            "season_reset": "🔄",
            "manual": "✍️",
        }

        return f"{icons.get(obj.reason, '')} {obj.get_reason_display()}"

    @admin.display(description="📊 Баланс")
    def score_flow(self, obj):
        return f"{obj.score_before} → {obj.score_after}"