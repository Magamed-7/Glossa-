from django.db import models
import uuid


class Reminder(models.Model):

    TYPE_CHOICES = [
        ('daily_review', 'Ежедневное повторение слов'),
        ('streak_warning', 'Предупреждение о потере серии'),
        ('inactivity', 'Долго не заходил'),
        ('new_content', 'Новый контент на твоём уровне'),
        ('subscription_expiring', 'Подписка истекает через 3 дня'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Ожидает отправки'),
        ('sent', 'Отправлено'),
        ('failed', 'Ошибка отправки'),
        ('skipped', 'Пропущено'),
    ]

    CHANNEL_CHOICES = [
        ('telegram', 'Telegram'),
        ('push', 'Push-уведомление'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    reminder_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    channel = models.CharField(
        max_length=15,
        choices=CHANNEL_CHOICES,
        default='telegram',
        verbose_name="Канал доставки"
    )
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reminders'
        verbose_name = 'Напоминание'
        verbose_name_plural = 'Напоминания'
        ordering = ['-scheduled_at']

    def __str__(self):
        return f'{self.user.email} — {self.reminder_type} — {self.status}'


class ReminderSchedule(models.Model):

    FREQUENCY_CHOICES = [
        ('daily', 'Каждый день'),
        ('every_2_days', 'Каждые 2 дня'),
        ('weekly', 'Каждую неделю'),
        ('smart', 'Умный — по активности'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reminder_schedule'
    )
    is_enabled = models.BooleanField(default=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    preferred_time = models.TimeField(default='09:00')
    timezone = models.CharField(max_length=50, default='UTC')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reminder_schedules'
        verbose_name = 'Расписание напоминаний'
        verbose_name_plural = 'Расписания напоминаний'

    def __str__(self):
        return f'{self.user.email} — {self.frequency} в {self.preferred_time}'