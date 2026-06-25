import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import PaymentEvent

logger = logging.getLogger('subscriptions')


@receiver(post_save, sender=PaymentEvent)
def activate_subscription_on_payment(sender, instance, **kwargs):
    if instance.status != 'success':
        return
    try:
        sub = instance.subscription
        now = timezone.now()
        sub.status = 'active'
        sub.started_at = now

        if sub.plan.plan_type == 'pro_monthly':
            sub.expires_at = now + relativedelta(months=1)
        elif sub.plan.plan_type == 'pro_yearly':
            sub.expires_at = now + relativedelta(years=1)

        sub.save()
        logger.info(
            f'Подписка активирована: {sub.user.email} — '
            f'{sub.plan.name} до {sub.expires_at.strftime("%d.%m.%Y")}'
        )
    except Exception as e:
        logger.error(
            f'Ошибка активации подписки для платежа {instance.id}: {e}', exc_info=True)