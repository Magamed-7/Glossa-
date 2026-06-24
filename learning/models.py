from django.db import models
from django.utils import timezone
import uuid


class UserPhrase(models.Model):

    SOURCE_CHOICES = [
        ('story', 'Из истории'),
        ('manual', 'Добавлено вручную'),
        ('grammar', 'Из урока грамматики'),
        ('duel', 'Из дуэли'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='phrases'
    )
    language = models.ForeignKey(
        'languages.Language',
        on_delete=models.PROTECT,
        related_name='user_phrases'
    )
    word = models.CharField(max_length=150)
    translation = models.CharField(max_length=255)
    context_sentence = models.TextField(blank=True)
    note = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')

    
    story_word = models.ForeignKey(
        'stories.StoryWord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_phrases'
    )
    grammar_lesson = models.ForeignKey(
        'grammar.GrammarLesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_phrases'
    )

    is_mastered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_phrases'
        verbose_name = 'Фраза пользователя'
        verbose_name_plural = 'Фразы пользователей'
        unique_together = ('user', 'word', 'language')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.word} → {self.translation}'


class ReviewSession(models.Model):

    RESULT_CHOICES = [
        ('again', 'Снова — не помню'),
        ('hard', 'Сложно'),
        ('good', 'Хорошо'),
        ('easy', 'Легко'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phrase = models.ForeignKey(
        UserPhrase,
        on_delete=models.CASCADE,
        related_name='review_sessions'
    )

    
    easiness_factor = models.FloatField(default=2.5)
    interval_days = models.PositiveIntegerField(default=1)
    repetitions = models.PositiveIntegerField(default=0)
    next_review_at = models.DateTimeField(default=timezone.now)
    last_result = models.CharField(
        max_length=10,
        choices=RESULT_CHOICES,
        null=True,
        blank=True
    )
    last_reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'review_sessions'
        verbose_name = 'Сессия повторения'
        verbose_name_plural = 'Сессии повторений'

    def __str__(self):
        return f'{self.phrase.word} — след. повторение: {self.next_review_at.date()}'

    def apply_sm2(self, quality: int):
        """
        quality: 0-5
        0-1 — не помню (again)
        2-3 — сложно (hard)
        4   — хорошо (good)
        5   — легко (easy)
        """
        if quality < 3:
            self.repetitions = 0
            self.interval_days = 1
        else:
            if self.repetitions == 0:
                self.interval_days = 1
            elif self.repetitions == 1:
                self.interval_days = 6
            else:
                self.interval_days = round(self.interval_days * self.easiness_factor)

            self.easiness_factor = max(
                1.3,
                self.easiness_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
            )
            self.repetitions += 1

        self.last_reviewed_at = timezone.now()
        self.next_review_at = timezone.now() + timezone.timedelta(days=self.interval_days)
        self.save()