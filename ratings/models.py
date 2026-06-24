from django.db import models
import uuid


class PlayerRating(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    language = models.ForeignKey(
        'languages.Language',
        on_delete=models.PROTECT,
        related_name='player_ratings'
    )
    score = models.PositiveIntegerField(default=1000)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    total_duels = models.PositiveIntegerField(default=0)
    win_streak = models.PositiveIntegerField(default=0)
    best_streak = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'player_ratings'
        verbose_name = 'Рейтинг игрока'
        verbose_name_plural = 'Рейтинги игроков'
        unique_together = ('user', 'language')
        ordering = ['-score']

    def __str__(self):
        return f'{self.user.email} | {self.language.name} | {self.score} очков'

    @property
    def win_rate(self):
        if self.total_duels == 0:
            return 0
        return round((self.wins / self.total_duels) * 100, 1)


class RatingHistory(models.Model):

    REASON_CHOICES = [
        ('duel_win', 'Победа в дуэли'),
        ('duel_loss', 'Поражение в дуэли'),
        ('duel_draw', 'Ничья'),
        ('season_reset', 'Сброс сезона'),
        ('manual', 'Ручная корректировка'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player_rating = models.ForeignKey(
        PlayerRating,
        on_delete=models.CASCADE,
        related_name='history'
    )
    duel = models.ForeignKey(
        'duels.Duel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rating_changes'
    )
    score_before = models.PositiveIntegerField()
    score_after = models.PositiveIntegerField()
    change = models.IntegerField()  
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='duel_win')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rating_history'
        verbose_name = 'История рейтинга'
        verbose_name_plural = 'История рейтингов'
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.change >= 0 else ''
        return f'{self.player_rating.user.email} | {sign}{self.change} | {self.reason}'