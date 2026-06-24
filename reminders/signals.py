import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import User
from .models import ReminderSchedule

logger = logging.getLogger('reminders')


@receiver(post_save, sender=User)
def create_reminder_schedule(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        ReminderSchedule.objects.create(user=instance)
        logger.info(f'ReminderSchedule создан для {instance.email}')
    except Exception as e:
        logger.error(f'Ошибка создания ReminderSchedule для {instance.email}: {e}', exc_info=True)