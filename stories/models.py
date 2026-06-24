from django.db import models
import uuid


class Story(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликована'),
        ('archived', 'Архив'),
    ]

    SOURCE_CHOICES = [
        ('manual', 'Вручную'),
        ('ai_generated', 'Сгенерирована AI'),
        ('imported', 'Импортирована'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    language = models.ForeignKey(
        'languages.Language',
        on_delete=models.PROTECT,
        related_name='stories'
    )
    cefr_level = models.ForeignKey(
        'languages.CEFRLevel',
        on_delete=models.PROTECT,
        related_name='stories'
    )
    topic = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_premium = models.BooleanField(default=False)
    read_time_minutes = models.PositiveSmallIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_stories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stories'
        verbose_name = 'История'
        verbose_name_plural = 'Истории'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} [{self.cefr_level.level}]'


class StoryWord(models.Model):

    PART_OF_SPEECH_CHOICES = [
        ('noun', 'Существительное'),
        ('verb', 'Глагол'),
        ('adjective', 'Прилагательное'),
        ('adverb', 'Наречие'),
        ('pronoun', 'Местоимение'),
        ('preposition', 'Предлог'),
        ('conjunction', 'Союз'),
        ('other', 'Другое'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name='words'
    )
    word = models.CharField(max_length=100)
    translation = models.CharField(max_length=255)
    context_sentence = models.TextField(blank=True)
    part_of_speech = models.CharField(
        max_length=20,
        choices=PART_OF_SPEECH_CHOICES,
        default='other'
    )
    difficulty = models.PositiveSmallIntegerField(default=1)
    audio_url = models.URLField(blank=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = 'story_words'
        verbose_name = 'Слово истории'
        verbose_name_plural = 'Слова историй'
        unique_together = ('story', 'word')

    def __str__(self):
        return f'{self.word} → {self.translation}'


class UserStoryProgress(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='story_progress'
    )
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name='user_progress'
    )
    is_completed = models.BooleanField(default=False)
    last_read_at = models.DateTimeField(auto_now=True)
    read_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'user_story_progress'
        verbose_name = 'Прогресс по истории'
        verbose_name_plural = 'Прогресс по историям'
        unique_together = ('user', 'story')

    def __str__(self):
        return f'{self.user.email} — {self.story.title}'