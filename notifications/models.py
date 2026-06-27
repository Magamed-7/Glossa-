from django.db import models
import uuid


class Notification(models.Model):

    TYPE_CHOICES = [
        ('duel_invite', 'Вызов на дуэль'),
        ('duel_finished', 'Дуэль завершена'),
        ('duel_cancelled', 'Дуэль отменена'),
        ('rating_changed', 'Изменение рейтинга'),
        ('achievement', 'Достижение'),
        ('friend_request', 'Запрос в друзья'),
        ('friend_accepted', 'Запрос в друзья принят'),
        ('subscription_expired', 'Подписка истекла'),
        ('subscription_expiring', 'Подписка скоро истечёт'),
        ('trial_expiring', 'Пробный период истекает'),
        ('new_story', 'Новая история'),
        ('review_ready', 'Слова к повторению'),
        ('system', 'Системное'),
    ]

    CHANNEL_CHOICES = [
        ('websocket', 'WebSocket'),
        ('telegram', 'Telegram'),
        ('push', 'Push-уведомление'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    channel = models.CharField(
        max_length=15,
        choices=CHANNEL_CHOICES,
        default='websocket',
    )

    
    duel = models.ForeignKey(
        'duels.Duel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    story = models.ForeignKey(
        'stories.Story',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    achievement = models.ForeignKey(
        'achievements.Achievement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.notification_type} — {"прочитано" if self.is_read else "новое"}'


class PushSubscription(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    endpoint = models.URLField(max_length=500)
    p256dh_key = models.CharField(max_length=255, blank=True, default='')
    auth_key = models.CharField(max_length=255, blank=True, default='')

    is_active = models.BooleanField(default=True)
    user_agent = models.CharField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'push_subscriptions'
        verbose_name = 'Push-подписка'
        verbose_name_plural = 'Push-подписки'
        unique_together = ('user', 'endpoint')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.endpoint[:50]}...'