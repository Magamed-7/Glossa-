from django.db import models
import uuid


class Notification(models.Model):

    TYPE_CHOICES = [
        ('duel_invite', 'Вызов на дуэль'),
        ('duel_finished', 'Дуэль завершена'),
        ('duel_cancelled', 'Дуэль отменена'),
        ('rating_changed', 'Изменение рейтинга'),
        ('achievement', 'Достижение'),
        ('subscription_expired', 'Подписка истекла'),
        ('subscription_expiring', 'Подписка скоро истечёт'),
        ('new_story', 'Новая история'),
        ('system', 'Системное'),
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

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.notification_type} — {"прочитано" if self.is_read else "новое"}'