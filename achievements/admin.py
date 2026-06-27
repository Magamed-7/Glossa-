from django.contrib import admin
from .models import Achievement, UserAchievement


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = (
        'icon',
        'title',
        'code',
        'category_badge',
        'created_at',
    )
    list_filter = (
        'category',
        'created_at',
    )
    search_fields = (
        'title',
        'code',
        'description',
    )
    ordering = ('category', 'title')
    readonly_fields = ('id', 'created_at')

    fieldsets = (
        ('🏆 Достижение', {
            'fields': (
                'code',
                'title',
                'description',
                'icon',
                'category',
            )
        }),
        ('⚙️ Условие', {
            'fields': (
                'condition',
            )
        }),
        ('⚙️ Система', {
            'fields': (
                'id',
                'created_at',
            )
        }),
    )

    @admin.display(description='Категория')
    def category_badge(self, obj):
        category_icons = {
            'levels': '🌱 CEFR',
            'reading': '📚 Чтение',
            'vocabulary': '📝 Словарь',
            'reviews': '🔄 Повторения',
            'streaks': '🔥 Стрики',
            'duels': '⚔️ Дуэли',
            'rating': '📈 Рейтинг',
            'grammar': '📐 Грамматика',
            'languages': '🌍 Языки',
            'ai': '🤖 AI тренер',
            'rare': '🍀 Редкое/Секретное',
        }
        return f'{category_icons.get(obj.category, "🏆")} {obj.get_category_display()}'


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'achievement_icon',
        'achievement_title',
        'achievement_category',
        'earned_at',
    )
    list_filter = (
        'achievement__category',
        'earned_at',
    )
    search_fields = (
        'user__username',
        'user__email',
        'achievement__title',
        'achievement__code',
    )
    autocomplete_fields = ('user', 'achievement')
    readonly_fields = ('id', 'earned_at')
    ordering = ('-earned_at',)

    fieldsets = (
        ('👤 Награждение', {
            'fields': (
                'user',
                'achievement',
            )
        }),
        ('⚙️ Система', {
            'fields': (
                'id',
                'earned_at',
            )
        }),
    )

    @admin.display(description='Иконка')
    def achievement_icon(self, obj):
        return obj.achievement.icon

    @admin.display(description='Достижение')
    def achievement_title(self, obj):
        return obj.achievement.title

    @admin.display(description='Категория')
    def achievement_category(self, obj):
        category_icons = {
            'levels': '🌱 CEFR',
            'reading': '📚 Чтение',
            'vocabulary': '📝 Словарь',
            'reviews': '🔄 Повторения',
            'streaks': '🔥 Стрики',
            'duels': '⚔️ Дуэли',
            'rating': '📈 Рейтинг',
            'grammar': '📐 Грамматика',
            'languages': '🌍 Языки',
            'ai': '🤖 AI тренер',
            'rare': '🍀 Редкое/Секретное',
        }
        return f'{category_icons.get(obj.achievement.category, "🏆")} {obj.achievement.get_category_display()}'
