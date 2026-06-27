from django.db import models
import uuid


class AIRequestLog(models.Model):

    REQUEST_TYPE_CHOICES = [
        ('generate_story', 'Генерация истории'),
        ('assist_story_creation', 'Помощь при создании истории'),
        ('explain_word', 'Объяснение слова'),
        ('explain_grammar', 'Объяснение грамматики'),
        ('generate_duel_question', 'Генерация вопроса для дуэли'),
        ('ai_duel_answer', 'Ответ AI тренера в дуэли'),
    ]

    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
        ('cached', 'Из кэша'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_requests'
    )
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPE_CHOICES)
    prompt = models.TextField()
    response = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    error_message = models.TextField(blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    response_time_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_request_logs'
        verbose_name = 'AI запрос'
        verbose_name_plural = 'AI запросы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.request_type} — {self.status} — {self.created_at.strftime("%d.%m.%Y %H:%M")}'