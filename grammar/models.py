from django.db import models
import uuid


class GrammarLesson(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
        ('archived', 'Архив'),
    ]

    SOURCE_CHOICES = [
        ('manual', 'Вручную'),
        ('ai_generated', 'Сгенерирован AI'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    language = models.ForeignKey(
        'languages.Language',
        on_delete=models.PROTECT,
        related_name='grammar_lessons'
    )
    cefr_level = models.ForeignKey(
        'languages.CEFRLevel',
        on_delete=models.PROTECT,
        related_name='grammar_lessons'
    )
    title = models.CharField(max_length=255)
    explanation = models.TextField()
    tip = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_premium = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    read_time_minutes = models.PositiveSmallIntegerField(default=0)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_lessons'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'grammar_lessons'
        verbose_name = 'Урок грамматики'
        verbose_name_plural = 'Уроки грамматики'
        ordering = ['order']

    def __str__(self):
        return f'{self.title} [{self.cefr_level.level}]'


class GrammarExample(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(
        GrammarLesson,
        on_delete=models.CASCADE,
        related_name='examples'
    )
    sentence = models.TextField()
    translation = models.TextField()
    explanation = models.TextField(blank=True)
    is_from_story = models.BooleanField(default=False)
    story = models.ForeignKey(
        'stories.Story',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grammar_examples'
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'grammar_examples'
        verbose_name = 'Пример'
        verbose_name_plural = 'Примеры'
        ordering = ['order']

    def __str__(self):
        return f'{self.lesson.title} — {self.sentence[:50]}'


class GrammarQuestion(models.Model):

    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Выбор ответа'),
        ('fill_blank', 'Заполни пропуск'),
        ('true_false', 'Правда / Ложь'),
        ('translate', 'Переведи'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(
        GrammarLesson,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    question_text = models.TextField()
    correct_answer = models.TextField()
    options = models.JSONField(default=list, blank=True)
    explanation = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'grammar_questions'
        verbose_name = 'Вопрос теста'
        verbose_name_plural = 'Вопросы тестов'
        ordering = ['order']

    def __str__(self):
        return f'{self.lesson.title} — вопрос {self.order}'


class UserGrammarProgress(models.Model):

    STATUS_CHOICES = [
        ('not_started', 'Не начат'),
        ('in_progress', 'В процессе'),
        ('completed', 'Завершён'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='grammar_progress'
    )
    lesson = models.ForeignKey(
        GrammarLesson,
        on_delete=models.CASCADE,
        related_name='user_progress'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    score = models.PositiveSmallIntegerField(default=0)
    max_score = models.PositiveSmallIntegerField(default=0)
    attempts = models.PositiveSmallIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_grammar_progress'
        verbose_name = 'Прогресс по грамматике'
        verbose_name_plural = 'Прогресс по грамматике'
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f'{self.user.email} — {self.lesson.title} — {self.status}'