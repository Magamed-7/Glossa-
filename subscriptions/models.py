from django.db import models
from django.utils import timezone
import uuid


class Plan(models.Model):

    PLAN_TYPE_CHOICES = [
        ('free', 'Бесплатный'),
        ('pro_monthly', 'Pro — месяц'),
        ('pro_yearly', 'Pro — год'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=5, default='USD')
    description = models.TextField(blank=True)

    # Limits
    stories_per_day = models.PositiveIntegerField(default=3)
    phrases_per_day = models.PositiveIntegerField(default=50)
    ai_access = models.BooleanField(default=False)
    rated_duels_access = models.BooleanField(default=False)
    full_analytics = models.BooleanField(default=False)
    full_catalog_access = models.BooleanField(default=False)

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
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
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
    ]

    PROVIDER_CHOICES = [
        ('mock', 'Тестовый'),
        ('stripe', 'Stripe'),
        ('telegram', 'Telegram Stars'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='mock')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=5, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider_payment_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_events'
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subscription.user.email} — {self.amount} {self.currency} — {self.status}'