from django.db import models
from django.utils import timezone
import uuid


class Plan(models.Model):

    PERIOD_CHOICES = [
        ('free', 'Free'),
        ('monthly', 'Monthly'),
        ('semi_annual', 'Semi-annual'),
        ('annual', 'Annual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=5, default='USD')
    description = models.TextField(blank=True, default='')

    stories_per_day = models.PositiveIntegerField(default=7)                              # Free: 7, Pro: безлимит
    phrases_per_day = models.PositiveIntegerField(default=55)                              # Free: 55, Pro: безлимит
    stories_per_week = models.PositiveIntegerField(default=4)                               # Free: 4 (B2+), Pro: безлимит
    rated_duels_access = models.BooleanField(default=False)
    global_leaderboard = models.BooleanField(default=False)
    ai_access = models.BooleanField(default=False)
    full_catalog_access = models.BooleanField(default=False)
    ai_story_assist = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'plans'
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'

    def __str__(self):
        return self.name



class Subscription(models.Model):

    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('expired', 'Истекла'),
        ('cancelled', 'Отменена'),
        ('pending', 'Ожидает оплаты'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_trial = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.plan.name}'

    @property
    def is_active(self):
        return (
            self.status == 'active' and
            self.expires_at is not None and
            self.expires_at > timezone.now()
        )




class PaymentEvent(models.Model):

    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
        ('refunded', 'Возврат'),
        ('pending', 'В обработке'),
        ('manual', 'Ручная оплата'),
    ]

    METHOD_CHOICES = [
        ('card', 'Карта'),
        ('bank_account', 'Банковский счёт'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')

    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='card')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=5, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    is_demo = models.BooleanField(default=False)

    provider_payment_id = models.CharField(max_length=255, blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_events'
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subscription.user.email} — {self.amount} {self.currency} ({self.status})'


class TrialPeriod(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='trial_period')
    subscription = models.OneToOneField(Subscription, on_delete=models.CASCADE, related_name='trial')

    started_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trial_periods'
        verbose_name = 'Пробный период'
        verbose_name_plural = 'Пробные периоды'

    def __str__(self):
        return f'Триал — {self.user.email}'

    @property
    def is_active(self):
        return (
            not self.is_used and
            self.expires_at is not None and
            self.expires_at > timezone.now()
        )