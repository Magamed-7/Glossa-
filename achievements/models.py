from django.db import models
import uuid


class Achievement(models.Model):
    CATEGORY_CHOICES = [
        ('levels', 'По уровням CEFR'),
        ('reading', 'По чтению историй'),
        ('vocabulary', 'По словарному запасу'),
        ('reviews', 'По повторениям (SM-2)'),
        ('streaks', 'По стрикам'),
        ('duels', 'По дуэлям'),
        ('rating', 'По рейтингу'),
        ('grammar', 'По грамматике'),
        ('languages', 'По языкам'),
        ('ai', 'По AI тренеру'),
        ('rare', 'Редкие / секретные'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True, verbose_name="Код")
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    icon = models.CharField(max_length=50, blank=True, default='', verbose_name="Иконка")
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        verbose_name="Категория"
    )
    condition = models.JSONField(default=dict, blank=True, verbose_name="Условие")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        db_table = 'achievements'
        verbose_name = 'Шаблон достижения'
        verbose_name_plural = 'Шаблоны достижений'
        ordering = ['category', 'title']

    def __str__(self):
        return f'{self.icon} {self.title} ({self.code})'


class UserAchievement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='achievements',
        verbose_name="Пользователь"
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='user_achievements',
        verbose_name="Достижение"
    )
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата получения")

    class Meta:
        db_table = 'user_achievements'
        verbose_name = 'Полученное достижение'
        verbose_name_plural = 'Полученные достижения'
        unique_together = ('user', 'achievement')
        ordering = ['-earned_at']

    def __str__(self):
        return f'{self.user.username} — {self.achievement.title}'
