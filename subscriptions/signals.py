from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import PaymentEvent


@receiver(post_save, sender=PaymentEvent)
def activate_subscription_on_payment(sender, instance, **kwargs):
    if instance.status == 'success':
        sub = instance.subscription
        now = timezone.now()
        sub.status = 'active'
        sub.started_at = now

        if sub.plan.plan_type == 'pro_monthly':
            sub.expires_at = now + relativedelta(months=1)
        elif sub.plan.plan_type == 'pro_yearly':
            sub.expires_at = now + relativedelta(years=1)

        sub.save()