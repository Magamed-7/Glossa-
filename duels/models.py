from django.db import models
import uuid


class Duel(models.Model):

    STATUS_CHOICES = [
        ('waiting', 'Ожидание противника'),
        ('in_progress', 'В процессе'),
        ('finished', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]

    MODE_CHOICES = [
        ('casual', 'Casual'),
        ('rated', 'Рейтинговая'),
    ]

    OPPONENT_CHOICES = [
        ('user', 'Игрок'),
        ('ai', 'AI тренер'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    player_one = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='duels_as_player_one')
    player_two = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='duels_as_player_two')

    language = models.ForeignKey('languages.Language', on_delete=models.PROTECT, related_name='duels')
    cefr_level = models.ForeignKey('languages.CEFRLevel', on_delete=models.PROTECT, related_name='duels')

    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='casual')
    opponent_type = models.CharField(max_length=10, choices=OPPONENT_CHOICES, default='user')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')

    total_rounds = models.PositiveSmallIntegerField(default=5)
    current_round = models.PositiveSmallIntegerField(default=0)
    time_per_round_seconds = models.PositiveSmallIntegerField(default=30)

    winner = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='won_duels')
    is_draw = models.BooleanField(default=False)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'duels'
        verbose_name = 'Дуэль'
        verbose_name_plural = 'Дуэли'
        ordering = ['-created_at']

    def __str__(self):
        opponent = self.player_two.email if self.player_two else ('AI' if self.opponent_type == 'ai' else '?')
        return f'Дуэль {self.player_one.email} vs {opponent} [{self.mode}]'

    @property
    def is_active(self):
        return self.status == 'in_progress'


class DuelRound(models.Model):

    ROUND_TYPE_CHOICES = [
        ('translate_word', 'Переведи слово'),
        ('choose_form', 'Выбери форму глагола'),
        ('build_sentence', 'Собери предложение'),
        ('fill_blank', 'Заполни пропуск'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    duel = models.ForeignKey(Duel, on_delete=models.CASCADE, related_name='rounds')
    round_number = models.PositiveSmallIntegerField()

    round_type = models.CharField(max_length=20, choices=ROUND_TYPE_CHOICES, default='translate_word')

    question_text = models.TextField()
    correct_answer = models.CharField(max_length=255)
    options = models.JSONField(default=list, blank=True)

    answer_player_one = models.CharField(max_length=255, blank=True, default='')
    answer_player_two = models.CharField(max_length=255, blank=True, default='')
    time_player_one = models.FloatField(null=True, blank=True)
    time_player_two = models.FloatField(null=True, blank=True)

    round_winner = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='won_rounds')
    is_draw = models.BooleanField(default=False)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    story_word = models.ForeignKey('stories.StoryWord', on_delete=models.SET_NULL, null=True, blank=True, related_name='duel_rounds')

    class Meta:
        db_table = 'duel_rounds'
        verbose_name = 'Раунд дуэли'
        verbose_name_plural = 'Раунды дуэлей'
        unique_together = ('duel', 'round_number')
        ordering = ['round_number']

    def __str__(self):
        return f'Дуэль {self.duel.id} — раунд {self.round_number}'


class DuelResult(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    duel = models.OneToOneField(Duel, on_delete=models.CASCADE, related_name='result')

    score_player_one = models.PositiveSmallIntegerField(default=0)
    score_player_two = models.PositiveSmallIntegerField(default=0)
    rating_change_player_one = models.IntegerField(default=0)
    rating_change_player_two = models.IntegerField(default=0)
    avg_time_player_one = models.FloatField(null=True, blank=True)
    avg_time_player_two = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'duel_results'
        verbose_name = 'Результат дуэли'
        verbose_name_plural = 'Результаты дуэлей'

    def __str__(self):
        return f'Результат: {self.duel}'